"""Tests for velbusaio.bus.manager.client.ManagerClient."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import aiohttp
import pytest

from fake_manager import FakeManager
from velbusaio.exceptions import VelbusAuthenticationFailed
from velbusaio.bus.manager.client import ManagerClient
from velbusaio.bus.manager.errors import VelbusManagerError

_INSTALLATION = json.loads(
    (Path(__file__).with_name("installation.json")).read_text()
)


@pytest.mark.asyncio
async def test_get_gateways(open_manager: FakeManager) -> None:
    """Gateways list matches the installation fixture."""
    client = ManagerClient(open_manager.host, open_manager.port)
    try:
        gateways = await client.get_gateways()
        assert len(gateways) == 1
        assert gateways[0]["id"] == "GWLOCAL"
        assert gateways[0]["isLocalGateway"] is True
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_actors_include_properties(open_manager: FakeManager) -> None:
    """Actors include channel property values when requested."""
    client = ManagerClient(open_manager.host, open_manager.port)
    try:
        actors = await client.get_actors("GWLOCAL", include_properties=True)
        assert actors[0]["moduleType"] == "VMB1RY"
        assert actors[0]["channels"][0]["properties"]["On"] is False
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_bearer_token_sent(open_manager: FakeManager) -> None:
    """The client attaches Authorization when an access token is set."""
    manager = FakeManager(
        _INSTALLATION, access_token="secret", require_auth=True
    )
    await manager.start()
    client = ManagerClient(manager.host, manager.port, access_token="secret")
    try:
        await client.get_gateways()
        assert manager.requests == []
        assert len(manager.installation["gateways"]) == 1
    finally:
        await client.close()
        await manager.stop()


@pytest.mark.asyncio
async def test_unauthorized_raises_authentication_failed() -> None:
    """HTTP 401 is mapped to VelbusAuthenticationFailed."""
    manager = FakeManager(
        _INSTALLATION, access_token="good", require_auth=True
    )
    await manager.start()
    client = ManagerClient(manager.host, manager.port, access_token="bad")
    try:
        with pytest.raises(VelbusAuthenticationFailed):
            await client.get_gateways()
    finally:
        await client.close()
        await manager.stop()


@pytest.mark.asyncio
async def test_other_http_error_raises_signum_error(
    open_manager: FakeManager,
) -> None:
    """Missing gateway returns VelbusManagerError with status."""
    client = ManagerClient(open_manager.host, open_manager.port)
    try:
        with pytest.raises(VelbusManagerError) as exc_info:
            await client.get_actors("missing")
        assert exc_info.value.status == 404
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_injectable_session_not_closed() -> None:
    """A caller-provided aiohttp session remains open after ManagerClient.close."""
    manager = FakeManager(_INSTALLATION)
    await manager.start()
    session = aiohttp.ClientSession()
    client = ManagerClient(manager.host, manager.port, session=session)
    try:
        await client.get_gateways()
        await client.close()
        assert not session.closed
    finally:
        await session.close()
        await manager.stop()


@pytest.mark.asyncio
async def test_invoke_action_and_set_property_recorded(
    open_manager: FakeManager,
) -> None:
    """POST actions and PUT properties hit the fake manager."""
    client = ManagerClient(open_manager.host, open_manager.port)
    try:
        await client.invoke_action("CHREL1", "On", {"Brightness": 80})
        await client.set_property("CHREL1", "Led", "On")
        methods = [r.method for r in open_manager.requests]
        assert methods == ["POST", "PUT"]
        assert open_manager.requests[0].body == {"On": {"input": {"Brightness": 80}}}
        assert open_manager.requests[1].body == {"Led": "On"}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_wait_for_gateway_actions_idle(open_manager: FakeManager) -> None:
    """Wait returns once a simulated Quickupdate action finishes."""
    client = ManagerClient(open_manager.host, open_manager.port)
    try:
        await client.gateway_action("GWLOCAL", "Quickupdate")
        await client.wait_for_gateway_actions_idle(
            "GWLOCAL",
            max_wait_seconds=5.0,
            poll_interval=0.01,
        )
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_websocket_receives_broadcast() -> None:
    """WebSocket listener receives propertyStatus pushes from the fake manager."""
    manager = FakeManager(_INSTALLATION)
    await manager.start()
    client = ManagerClient(manager.host, manager.port)
    received: asyncio.Queue[dict[str, object]] = asyncio.Queue()

    async def on_message(data: dict[str, object]) -> None:
        await received.put(data)

    try:
        await client.run_websocket(on_message)
        # Allow the background task to connect.
        for _ in range(50):
            if manager._ws_clients:
                break
            await asyncio.sleep(0.05)
        assert manager._ws_clients, "WebSocket did not connect"

        payload = {
            "messageType": "propertyStatus",
            "thingId": "CHREL1",
            "data": {"On": True},
        }
        await manager.broadcast(payload)
        msg = await asyncio.wait_for(received.get(), timeout=2.0)
        assert msg == payload
    finally:
        await client.close()
        await manager.stop()
