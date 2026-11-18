"""aiohttp client for the Signum Manager REST API and WebSocket feed."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
import logging
from typing import Any, cast

import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType

from velbusaio.bus.manager.errors import VelbusManagerError
from velbusaio.exceptions import VelbusAuthenticationFailed

_LOGGER = logging.getLogger(__name__)

MessageCallback = Callable[[dict[str, Any]], Awaitable[None] | None]
DisconnectCallback = Callable[[], Awaitable[None] | None]

_WS_BACKOFF_MIN = 1.0
_WS_BACKOFF_MAX = 30.0
_WS_HEARTBEAT = 30.0
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30.0)
_GATEWAY_ACTION_POLL_INTERVAL = 2.0
_GATEWAY_ACTION_IDLE_TIMEOUT = 600.0
_GATEWAY_ACTION_START_GRACE = 10.0


class ManagerClient:
    """REST and WebSocket client for Signum Manager API v2."""

    def __init__(
        self,
        host: str,
        port: int,
        session: ClientSession | None = None,
        access_token: str | None = None,
    ) -> None:
        """Initialize the client."""
        self._host = host
        self._port = port
        self._access_token = access_token
        self._owns_session = session is None
        self._session = session or ClientSession(timeout=_REQUEST_TIMEOUT)
        self._stop_ws = asyncio.Event()
        self._ws_task: asyncio.Task[None] | None = None
        self._ws: ClientWebSocketResponse | None = None
        self._ws_connected = asyncio.Event()

    @property
    def session(self) -> ClientSession:
        """Return the aiohttp session used for REST calls."""
        return self._session

    def _rest_url(self, path: str) -> str:
        return f"http://{self._host}:{self._port}/velbus/api/v2{path}"

    def _ws_url(self) -> str:
        return f"ws://{self._host}:{self._port}/velbus/api/v2/ws"

    def _auth_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = dict(extra or {})
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def close(self) -> None:
        """Stop the WebSocket task and close an owned HTTP session."""
        await self.stop_websocket()
        if self._owns_session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        headers = self._auth_headers(
            {"Content-Type": "application/json"} if json_body is not None else None
        )
        try:
            async with self._session.request(
                method,
                self._rest_url(path),
                headers=headers,
                params=params,
                json=json_body,
            ) as response:
                if response.status == 401:
                    raise VelbusAuthenticationFailed
                if response.status >= 400:
                    body = await response.text()
                    raise VelbusManagerError(
                        f"Signum API {method} {path} failed: "
                        f"HTTP {response.status} {body}",
                        status=response.status,
                    )
                if response.status == 204:
                    return None
                raw = await response.read()
                if not raw:
                    return None
                return json.loads(raw.decode())
        except (TimeoutError, aiohttp.ClientError) as exc:
            raise VelbusManagerError(
                f"Signum API {method} {path} failed: {exc}"
            ) from exc

    async def get_gateways(self) -> list[dict[str, Any]]:
        """Return all Velbus gateways known to the manager."""
        result = await self._request("GET", "/gateways")
        return cast("list[dict[str, Any]]", result)

    async def get_actors(
        self, gateway_id: str, *, include_properties: bool = True
    ) -> list[dict[str, Any]]:
        """Return modules for a gateway, optionally with property values."""
        params = {"includeProperties": "true"} if include_properties else None
        result = await self._request(
            "GET", f"/gateways/{gateway_id}/actors", params=params
        )
        return cast("list[dict[str, Any]]", result)

    async def invoke_action(
        self,
        thing_id: str,
        action_name: str,
        inputs: dict[str, Any] | None = None,
    ) -> None:
        """POST an action on a thing (module, channel, or gateway)."""
        body = {action_name: {"input": inputs or {}}}
        await self._request(
            "POST",
            f"/things/{thing_id}/actions/{action_name}",
            json_body=body,
        )

    async def set_property(self, thing_id: str, prop_name: str, value: Any) -> None:
        """PUT a property value on a thing."""
        await self._request(
            "PUT",
            f"/things/{thing_id}/properties/{prop_name}",
            json_body={prop_name: value},
        )

    async def gateway_action(
        self,
        gateway_id: str,
        action_name: str,
        inputs: dict[str, Any] | None = None,
    ) -> None:
        """Run a gateway-level action (for example ``Quickupdate``)."""
        await self.invoke_action(gateway_id, action_name, inputs)

    async def get_running_actions(self, thing_id: str) -> list[dict[str, Any]]:
        """Return queued or running actions for a thing (empty when idle)."""
        result = await self._request("GET", f"/things/{thing_id}/actions")
        if not result:
            return []
        return cast("list[dict[str, Any]]", result)

    async def wait_for_gateway_actions_idle(
        self,
        gateway_id: str,
        *,
        max_wait_seconds: float = _GATEWAY_ACTION_IDLE_TIMEOUT,
        poll_interval: float = _GATEWAY_ACTION_POLL_INTERVAL,
    ) -> None:
        """Poll until the manager reports no running actions on the gateway."""
        loop = asyncio.get_running_loop()
        started = loop.time()
        deadline = started + max_wait_seconds
        saw_busy = False
        while loop.time() < deadline:
            actions = await self.get_running_actions(gateway_id)
            if actions:
                saw_busy = True
            elif saw_busy:
                return
            if not saw_busy and loop.time() - started >= _GATEWAY_ACTION_START_GRACE:
                _LOGGER.debug(
                    "Gateway %s reported no queued actions after %.0fs",
                    gateway_id,
                    _GATEWAY_ACTION_START_GRACE,
                )
                return
            await asyncio.sleep(poll_interval)
        _LOGGER.warning(
            "Gateway %s actions still running after %.0fs; continuing",
            gateway_id,
            max_wait_seconds,
        )

    async def wait_websocket(self, max_wait_seconds: float = 5.0) -> None:
        """Block until the WebSocket has connected or the wait budget elapses."""
        await asyncio.wait_for(self._ws_connected.wait(), max_wait_seconds)

    async def run_websocket(
        self,
        on_message: MessageCallback,
        on_disconnect: DisconnectCallback | None = None,
    ) -> None:
        """Connect to the push WebSocket and reconnect with backoff until stopped."""
        if self._ws_task is not None:
            return
        self._stop_ws.clear()
        self._ws_task = asyncio.create_task(
            self._websocket_loop(on_message, on_disconnect),
            name="manager-websocket",
        )

    async def stop_websocket(self) -> None:
        """Cancel the WebSocket background task."""
        self._stop_ws.set()
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        if self._ws_task is not None:
            await self._ws_task
            self._ws_task = None
        self._ws = None

    async def _websocket_loop(
        self,
        on_message: MessageCallback,
        on_disconnect: DisconnectCallback | None,
    ) -> None:
        backoff = _WS_BACKOFF_MIN
        while not self._stop_ws.is_set():
            try:
                async with self._session.ws_connect(
                    self._ws_url(),
                    heartbeat=_WS_HEARTBEAT,
                ) as ws:
                    self._ws = ws
                    self._ws_connected.set()
                    backoff = _WS_BACKOFF_MIN
                    async for msg in ws:
                        if self._stop_ws.is_set():
                            break
                        if msg.type == WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            await self._call_callback(on_message, data)
                        elif msg.type in {
                            WSMsgType.CLOSE,
                            WSMsgType.CLOSED,
                            WSMsgType.ERROR,
                        }:
                            break
            except asyncio.CancelledError:
                raise
            except (aiohttp.ClientError, TimeoutError, json.JSONDecodeError, OSError):
                _LOGGER.debug("Signum WebSocket disconnected", exc_info=True)
            finally:
                self._ws = None
                self._ws_connected.clear()
                if on_disconnect is not None:
                    await self._call_callback(on_disconnect)

            if self._stop_ws.is_set():
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, _WS_BACKOFF_MAX)

    @staticmethod
    async def _call_callback(
        callback: MessageCallback | DisconnectCallback,
        *args: Any,
    ) -> None:
        result = callback(*args)
        if asyncio.iscoroutine(result):
            await result
