"""Minimal aiohttp Signum Manager stand-in for tests."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp import web

_DEFAULT_INSTALLATION = Path(__file__).with_name("installation.json")


@dataclass
class RecordedRequest:
    """A REST call captured by the fake manager."""

    method: str
    path: str
    body: Any | None
    headers: Mapping[str, str]


class FakeManager:
    """In-process Signum Manager with REST routes and a broadcast WebSocket."""

    def __init__(
        self,
        installation: dict[str, Any] | None = None,
        *,
        access_token: str | None = None,
        require_auth: bool = False,
    ) -> None:
        """Build a manager from an installation dict or the default fixture."""
        if installation is None:
            installation = json.loads(_DEFAULT_INSTALLATION.read_text())
        self.installation = installation
        self.access_token = access_token
        self.require_auth = require_auth
        self.requests: list[RecordedRequest] = []
        self.modules_by_gateway: dict[str, list[dict[str, Any]]] = {}
        self.websocket_gateway_ids: list[str | None] = []
        self._running_actions: dict[str, list[str]] = {}
        self._ws_clients: set[web.WebSocketResponse] = set()
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self.host = "127.0.0.1"
        self.port = 0

    @property
    def base_url(self) -> str:
        """HTTP authority (host:port) for the listening server."""
        return f"{self.host}:{self.port}"

    def _check_auth(self, request: web.Request) -> None:
        if not self.require_auth:
            return
        expected = f"Bearer {self.access_token}"
        if request.headers.get("Authorization") != expected:
            raise web.HTTPUnauthorized(text="Invalid token")

    def _record(self, request: web.Request, body: Any | None) -> None:
        self.requests.append(
            RecordedRequest(
                method=request.method,
                path=request.path,
                body=body,
                headers=dict(request.headers),
            )
        )

    async def _handle_gateways(self, request: web.Request) -> web.Response:
        self._check_auth(request)
        return web.json_response(self.installation["gateways"])

    async def _handle_actors(self, request: web.Request) -> web.Response:
        self._check_auth(request)
        gateway_id = request.match_info["gateway_id"]
        gateway_ids = {g["id"] for g in self.installation["gateways"]}
        if gateway_id not in gateway_ids:
            raise web.HTTPNotFound()
        modules = self.modules_by_gateway.get(gateway_id, self.installation["modules"])
        if request.query.get("includeProperties", "").lower() == "true":
            return web.json_response(modules)
        stripped: list[dict[str, Any]] = []
        for module in modules:
            copy = dict(module)
            copy.pop("properties", None)
            channels = []
            for channel in module.get("channels", []):
                ch = dict(channel)
                ch.pop("properties", None)
                channels.append(ch)
            copy["channels"] = channels
            stripped.append(copy)
        return web.json_response(stripped)

    async def _simulate_gateway_action(self, thing_id: str, action_name: str) -> None:
        queue = self._running_actions.setdefault(thing_id, [])
        queue.append(action_name)
        try:
            await asyncio.sleep(0.05)
        finally:
            queue.remove(action_name)
            if not queue:
                self._running_actions.pop(thing_id, None)

    async def _handle_get_actions(self, request: web.Request) -> web.Response:
        self._check_auth(request)
        thing_id = request.match_info["thing_id"]
        names = self._running_actions.get(thing_id, [])
        return web.json_response([{name: {"status": "running"}} for name in names])

    async def _handle_action(self, request: web.Request) -> web.Response:
        self._check_auth(request)
        body = None
        if request.can_read_body:
            body = await request.json()
        self._record(request, body)
        thing_id = request.match_info["thing_id"]
        action_name = request.match_info["action_name"]
        if action_name == "Quickupdate":
            asyncio.create_task(
                self._simulate_gateway_action(thing_id, action_name),
                name="fake-quickupdate",
            )
        return web.Response(status=201)

    async def _handle_property(self, request: web.Request) -> web.Response:
        self._check_auth(request)
        body = await request.json()
        self._record(request, body)
        return web.Response(status=200)

    async def _handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        self._check_auth(request)
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)
        self._ws_clients.add(ws)
        self.websocket_gateway_ids.append(request.query.get("gatewayId"))
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.ERROR:
                    break
        finally:
            self._ws_clients.discard(ws)
        return ws

    async def start(self) -> tuple[str, int]:
        """Start the HTTP server on a random port."""
        app = web.Application()
        app.router.add_get("/velbus/api/v2/gateways", self._handle_gateways)
        app.router.add_get(
            "/velbus/api/v2/gateways/{gateway_id}/actors", self._handle_actors
        )
        app.router.add_get(
            "/velbus/api/v2/things/{thing_id}/actions",
            self._handle_get_actions,
        )
        app.router.add_post(
            "/velbus/api/v2/things/{thing_id}/actions/{action_name}",
            self._handle_action,
        )
        app.router.add_put(
            "/velbus/api/v2/things/{thing_id}/properties/{prop_name}",
            self._handle_property,
        )
        app.router.add_get("/velbus/api/v2/ws", self._handle_ws)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, 0)
        await self._site.start()
        assert self._site._server is not None
        sock = self._site._server.sockets[0]
        self.port = sock.getsockname()[1]
        return self.host, self.port

    async def disconnect_websockets(self) -> None:
        """Close current connections while leaving the HTTP server running."""
        for ws in list(self._ws_clients):
            await ws.close()
        self._ws_clients.clear()

    async def stop(self) -> None:
        """Shut down WebSocket clients and the HTTP server."""
        await self.disconnect_websockets()
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
            self._site = None

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Push a JSON message to every connected WebSocket client."""
        if not self._ws_clients:
            return
        payload = json.dumps(message)
        dead: list[web.WebSocketResponse] = []
        for ws in self._ws_clients:
            try:
                await ws.send_str(payload)
            except ConnectionError:
                dead.append(ws)
        for ws in dead:
            self._ws_clients.discard(ws)
