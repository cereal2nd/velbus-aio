"""Gateway selection, isolation, and compatibility for Manager controllers."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from copy import deepcopy
from pathlib import Path
from urllib.parse import quote

import pytest
import pytest_asyncio

from fake_manager import FakeManager
from velbusaio.controller import Velbus
from velbusaio.exceptions import VelbusConnectionFailed
from velbusaio.messages.switch_relay_on import SwitchRelayOnMessage


@pytest_asyncio.fixture
async def two_buses() -> AsyncIterator[FakeManager]:
    """Serve two gateways, both with a relay at address 5, channel 1."""
    manager = FakeManager(access_token="test-token")
    local = manager.installation["gateways"][0]
    remote = {**local, "id": "GWREMOTE", "isLocalGateway": False}
    manager.installation["gateways"] = [remote, local]
    remote_modules = deepcopy(manager.installation["modules"])
    remote_modules[0]["id"] = "MODREMOTE"
    channel = remote_modules[0]["channels"][0]
    channel.update(id="CHREMOTE", parentId="MODREMOTE")
    manager.modules_by_gateway[remote["id"]] = remote_modules
    await manager.start()
    try:
        yield manager
    finally:
        await manager.stop()


@pytest_asyncio.fixture
async def remote_bus(two_buses: FakeManager, tmp_path: Path) -> AsyncIterator[Velbus]:
    """Build an independent controller for the non-local gateway."""
    controller = Velbus(
        f"manager://{two_buses.base_url}/GWREMOTE",
        cache_dir=str(tmp_path),
        access_token=two_buses.access_token,
    )
    try:
        yield controller
    finally:
        await controller.stop()


async def _wait_until(predicate: Callable[[], bool]) -> None:
    async with asyncio.timeout(10):
        while not predicate():
            await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_two_controllers_route_commands(
    two_buses: FakeManager, tmp_path: Path
) -> None:
    """The automatic and explicitly selected buses each control their own relay."""
    dsn = f"manager://{two_buses.base_url}"
    local = Velbus(dsn, cache_dir=str(tmp_path))
    remote = Velbus(f"{dsn}/GWREMOTE", cache_dir=str(tmp_path))
    try:
        for controller in (local, remote):
            await controller.connect()
            await controller.start()
        assert local.manager_backend.gateway_id == "GWLOCAL"
        assert remote.manager_backend.gateway_id == "GWREMOTE"
        assert two_buses.websocket_gateway_ids == [None, "GWREMOTE"]
        command = SwitchRelayOnMessage(address=5)
        command.relay_channels = [1]
        await local.send(command)
        await remote.send(command)
        await remote.scan()
        assert [request.path for request in two_buses.requests] == [
            "/velbus/api/v2/things/CHREL1/actions/On",
            "/velbus/api/v2/things/CHREMOTE/actions/On",
            "/velbus/api/v2/things/GWREMOTE/actions/Quickupdate",
        ]
    finally:
        await remote.stop()
        await local.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("suffix", ["", "/"])
async def test_automatic_selection_without_local_gateway(
    two_buses: FakeManager, tmp_path: Path, suffix: str
) -> None:
    """Existing installations fall back to the first Velbus gateway."""
    for gateway in two_buses.installation["gateways"]:
        gateway["isLocalGateway"] = False
    controller = Velbus(
        f"manager://{two_buses.base_url}{suffix}", cache_dir=str(tmp_path)
    )
    try:
        await controller.connect()
        assert controller.manager_backend.gateway_id == "GWREMOTE"
        assert two_buses.websocket_gateway_ids == [None]
    finally:
        await controller.stop()


@pytest.mark.asyncio
async def test_missing_gateway_never_connects_to_another_bus(
    two_buses: FakeManager, tmp_path: Path
) -> None:
    """An explicit ID must exist before opening a socket or sending an action."""
    controller = Velbus(
        f"manager://{two_buses.base_url}/missing",
        cache_dir=str(tmp_path),
    )
    try:
        with pytest.raises(VelbusConnectionFailed):
            await controller.connect()
        assert controller.manager_backend.gateway_id is None
        assert two_buses.websocket_gateway_ids == []
        assert two_buses.requests == []
    finally:
        await controller.stop()


@pytest.mark.asyncio
async def test_gateway_id_is_one_encoded_segment(
    two_buses: FakeManager, tmp_path: Path
) -> None:
    """A gateway ID survives DSN, REST path and WebSocket query encoding."""
    gateway_id = "floor/A?west#1 +%2F"
    two_buses.installation["gateways"][0]["id"] = gateway_id
    two_buses.modules_by_gateway[gateway_id] = two_buses.modules_by_gateway.pop(
        "GWREMOTE"
    )
    dsn = f"manager://{two_buses.base_url}/{quote(gateway_id, safe='')}"
    controller = Velbus(dsn, cache_dir=str(tmp_path))
    try:
        await controller.connect()
        await controller.start()
        assert controller.manager_backend.gateway_id == gateway_id
        assert controller.manager_backend.thing_id_for(5, 1) == "CHREMOTE"
        assert two_buses.websocket_gateway_ids == [gateway_id]
        await controller.scan()
        assert [r.path for r in two_buses.requests] == [
            f"/velbus/api/v2/things/{gateway_id}/actions/Quickupdate"
        ]
    finally:
        await controller.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/GWREMOTE/extra", "//", "/.", "/..", "/%2E%2e"])
async def test_rejects_invalid_gateway_path(
    two_buses: FakeManager, tmp_path: Path, path: str
) -> None:
    """Ambiguous or relative paths fail before any bus is selected."""
    with pytest.raises(ValueError):
        Velbus(f"manager://{two_buses.base_url}{path}", cache_dir=str(tmp_path))


@pytest.mark.asyncio
async def test_select_gateway_with_ipv6_literal(
    two_buses: FakeManager, tmp_path: Path
) -> None:
    """Use an IPv4-mapped IPv6 authority to reach the test server over REST and WS."""
    controller = Velbus(
        f"manager://[::ffff:127.0.0.1]:{two_buses.port}/GWREMOTE",
        cache_dir=str(tmp_path),
    )
    try:
        await controller.connect()
        await controller.start()
        assert controller.manager_backend.gateway_id == "GWREMOTE"
        assert two_buses.websocket_gateway_ids == ["GWREMOTE"]
        assert controller.manager_backend.thing_id_for(5, 1) == "CHREMOTE"
    finally:
        await controller.stop()


@pytest.mark.asyncio
async def test_connects_only_the_selected_offline_gateway(
    two_buses: FakeManager, remote_bus: Velbus
) -> None:
    """An offline secondary bus receives the Connect action addressed to its ID."""
    two_buses.installation["gateways"][0]["state"] = "Disconnected"

    async def acknowledge_connect() -> None:
        await _wait_until(lambda: bool(two_buses.requests))
        assert [r.path for r in two_buses.requests] == [
            "/velbus/api/v2/things/GWREMOTE/actions/Connect"
        ]
        await two_buses.broadcast(
            {
                "messageType": "gatewayStatus",
                "gatewayId": "GWREMOTE",
                "thingId": "GWREMOTE",
                "data": {"state": "Connected"},
            }
        )

    async with asyncio.timeout(5), asyncio.TaskGroup() as tasks:
        tasks.create_task(remote_bus.connect())
        tasks.create_task(acknowledge_connect())
    assert remote_bus.connected


@pytest.mark.asyncio
async def test_reconnect_keeps_selected_gateway(
    two_buses: FakeManager, remote_bus: Velbus
) -> None:
    """Every handshake, including reconnect, selects the gateway and authenticates."""
    two_buses.require_auth = True
    modules = two_buses.modules_by_gateway["GWREMOTE"]
    two_buses.modules_by_gateway["GWREMOTE"] = []
    await remote_bus.connect()
    await remote_bus.start()
    assert not remote_bus.get_modules()
    two_buses.modules_by_gateway["GWREMOTE"] = modules
    await two_buses.disconnect_websockets()
    await _wait_until(lambda: remote_bus.connected and 5 in remote_bus.get_modules())
    assert two_buses.websocket_gateway_ids == ["GWREMOTE", "GWREMOTE"]


@pytest.mark.asyncio
async def test_disappearing_gateway_cannot_rebind_to_local(
    two_buses: FakeManager, remote_bus: Velbus
) -> None:
    """Retry a missing gateway without reusing its old channel or the other bus."""
    await remote_bus.connect()
    await remote_bus.start()
    backend = remote_bus.manager_backend
    assert backend.thing_id_for(5, 1) == "CHREMOTE"
    gateways = two_buses.installation["gateways"]
    selected = gateways.pop(0)
    await two_buses.disconnect_websockets()
    # A second retry means the first reopened socket failed gateway validation.
    await _wait_until(lambda: len(two_buses.websocket_gateway_ids) >= 3)
    assert not remote_bus.connected
    assert backend.thing_id_for(5, 1) is None
    assert two_buses.requests == []

    gateways.append(selected)
    await _wait_until(lambda: remote_bus.connected)
    assert set(two_buses.websocket_gateway_ids) == {"GWREMOTE"}
    assert backend.thing_id_for(5, 1) == "CHREMOTE"


@pytest.mark.asyncio
async def test_events_are_isolated_on_a_shared_feed(
    two_buses: FakeManager, remote_bus: Velbus
) -> None:
    """Tagged events and older untagged broadcasts affect only their own bus."""
    states = []

    async def state_changed() -> None:
        states.append(remote_bus.connected)

    await remote_bus.connect()
    await remote_bus.start()
    relay = remote_bus.get_modules()[5].get_channels()[1]
    remote_bus.add_connect_callback(state_changed)
    remote_bus.add_disconnect_callback(state_changed)

    def gateway_status(thing: str, state: str) -> dict:
        return {
            "messageType": "gatewayStatus",
            "thingId": thing,
            "data": {"state": state},
        }

    def property_status(thing: str, on: bool) -> dict:
        return {
            "messageType": "propertyStatus",
            "thingId": thing,
            "data": {"On": on},
        }

    for event in (
        gateway_status("GWLOCAL", "Disconnected"),
        gateway_status("GWLOCAL", "Connected"),
        gateway_status("GWREMOTE", "Disconnected"),
        property_status("CHREL1", True),
        {**property_status("CHREMOTE", False), "gatewayId": "GWLOCAL"},
        gateway_status("GWREMOTE", "Disconnected"),
        property_status("CHREMOTE", True),
    ):
        await two_buses.broadcast(event)
    await _wait_until(relay.is_on)
    assert states == [False, True]

    await two_buses.broadcast(
        {**property_status("CHREMOTE", False), "gatewayId": "GWLOCAL"}
    )
    await two_buses.broadcast(
        {**gateway_status("GWREMOTE", "Disconnected"), "gatewayId": "GWREMOTE"}
    )
    await _wait_until(lambda: not remote_bus.connected)
    assert relay.is_on()


@pytest.mark.asyncio
async def test_stale_manager_module_preserves_shared_cache(
    two_buses: FakeManager, tmp_path: Path, remote_bus: Velbus
) -> None:
    """Dropping a Manager module preserves another controller's address cache."""
    await remote_bus.connect()
    await remote_bus.start()
    assert 5 in remote_bus.get_modules()
    cache_file = tmp_path / "5.json"
    cache_file.write_text("{}")
    two_buses.modules_by_gateway["GWREMOTE"] = []
    await remote_bus.start()
    assert 5 not in remote_bus.get_modules()
    assert cache_file.read_text() == "{}"
