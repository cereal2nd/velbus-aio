"""Signum Manager backend for :class:`~velbusaio.controller.Velbus`."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import datetime
import logging
from typing import TYPE_CHECKING, Any

from aiohttp import ClientSession

from velbusaio.bus.manager.client import ManagerClient
from velbusaio.bus.manager.commands import ManagerCommandTranslator
from velbusaio.bus.manager.mapping import (
    manager_module_type_to_code,
    map_module_properties,
    map_properties_to_update,
    parse_build_number,
    remap_channel_number,
)
from velbusaio.channels import Dimmer
from velbusaio.exceptions import (
    VelbusAuthenticationFailed,
    VelbusConnectionFailed,
    VelbusNotSupported,
)
from velbusaio.message import Message

if TYPE_CHECKING:
    from velbusaio.controller import Velbus

_LOGGER = logging.getLogger(__name__)

AuthFailedCallback = Callable[[], Awaitable[None] | None]

_GATEWAY_CONNECTED = "Connected"
_GATEWAY_UP_STATES = frozenset({"Connected", "Done", "21"})
_GATEWAY_DOWN_STATES = frozenset(
    {"Disconnected", "Disconnecting", "Closed", "50", "40", "60"}
)


def _gateway_link_up(state: object) -> bool | None:
    """Interpret Signum gateway *state*; None means unknown (do not change link)."""
    if state is None:
        return None
    if isinstance(state, int):
        if state == 21:
            return True
        if state in (40, 50, 60):
            return False
        return None
    text = str(state)
    if text in _GATEWAY_UP_STATES:
        return True
    if text in _GATEWAY_DOWN_STATES:
        return False
    return None


class ManagerBackend:
    """Velbus controller backend that talks to Signum Manager over HTTP/WebSocket."""

    def __init__(
        self,
        controller: Velbus,
        host: str,
        port: int,
        session: ClientSession | None,
        access_token: str | None,
    ) -> None:
        """Attach to Signum Manager at *host*:*port* for *controller*."""
        self.controller = controller
        self._host = host
        self._port = port
        self._access_token = access_token
        self._client = ManagerClient(
            host, port, session=session, access_token=access_token
        )
        self._translator = ManagerCommandTranslator(self)
        self._gateway_id: str | None = None
        self._channel_things: dict[tuple[int, int], str] = {}
        self._thing_channels: dict[str, tuple[int, int]] = {}
        self._module_things: dict[int, str] = {}
        self._auth_failed_callbacks: list[AuthFailedCallback] = []
        self._available = False
        self._bus_connected = True
        self._logged_manager_unavailable = False
        self._logged_bus_unavailable = False
        self._snapshot_lock = asyncio.Lock()
        self._bus_link_ready = asyncio.Event()

    @property
    def client(self) -> ManagerClient:
        """Return the REST/WebSocket client."""
        return self._client

    @property
    def is_connected(self) -> bool:
        """True when the manager is reachable and the Velbus link is up."""
        return self._available and self._bus_connected

    @property
    def manager_available(self) -> bool:
        """True when the Signum Manager WebSocket/REST session is up."""
        return self._available

    async def wait_for_bus_link(self, max_wait_seconds: float = 60.0) -> bool:
        """Wait until the manager reports a live Velbus gateway link."""
        if self._bus_connected:
            return True
        try:
            await asyncio.wait_for(
                self._bus_link_ready.wait(), timeout=max_wait_seconds
            )
        except TimeoutError:
            return False
        return self._bus_connected

    def _sync_bus_link_event(self) -> None:
        if self._bus_connected:
            self._bus_link_ready.set()
        else:
            self._bus_link_ready.clear()

    def add_auth_failed_callback(self, meth: AuthFailedCallback) -> None:
        """Register a coroutine when the access token is rejected."""
        self._auth_failed_callbacks.append(meth)

    def remove_auth_failed_callback(self, meth: AuthFailedCallback) -> None:
        """Remove an auth-failed callback."""
        self._auth_failed_callbacks.remove(meth)

    def thing_id_for(self, address: int, channel: int) -> str | None:
        """Return the Signum thing id for a module address and channel number."""
        return self._channel_things.get((address, channel))

    def module_thing_id(self, address: int) -> str | None:
        """Return the Signum thing id for a module."""
        return self._module_things.get(address)

    async def connect(self) -> None:
        """Open the WebSocket feed and verify the manager responds."""
        try:
            gateways = await self._client.get_gateways()
        except VelbusAuthenticationFailed:
            await self._fire_auth_failed()
            raise
        except Exception as err:
            raise VelbusConnectionFailed from err

        local = next((g for g in gateways if g.get("isLocalGateway")), None)
        if local is None:
            local = next(
                (g for g in gateways if g.get("type") == "velbusgateway"), None
            )
        if local is None:
            raise VelbusConnectionFailed
        self._gateway_id = str(local["id"])
        link = _gateway_link_up(local.get("state"))
        if link is True:
            self._bus_connected = True
        elif link is False:
            self._bus_connected = False
        self._sync_bus_link_event()

        await self._client.run_websocket(self._on_ws_message, self._on_ws_disconnect)
        await self._client.wait_websocket()
        await self._set_manager_available(True)

        if not self._bus_connected:
            _LOGGER.info(
                "Signum gateway %s Velbus link state is %r; requesting Connect",
                self._gateway_id,
                local.get("state"),
            )
            try:
                await self._client.gateway_action(self._gateway_id, "Connect")
            except Exception:
                _LOGGER.exception("Signum gateway Connect action failed")
            else:
                if not await self.wait_for_bus_link(max_wait_seconds=60.0):
                    _LOGGER.warning(
                        "Signum gateway %s is still not Connected; "
                        "commands may fail until the manager reaches the Velbus "
                        "gateway (check TLS, port 27015, HA).",
                        self._gateway_id,
                    )

    async def start(self) -> None:
        """Load the installation snapshot and build module objects."""
        await self._apply_snapshot()
        await self.controller.notify_scan_complete(set(self.controller.get_modules()))

    async def stop(self) -> None:
        """Shut down the WebSocket task and close an owned HTTP session."""
        await self._set_manager_available(False)
        await self._client.close()

    async def scan(self) -> None:
        """Run Quickupdate on the gateway and refresh the installation snapshot."""
        if self._gateway_id is None:
            return
        await self._client.gateway_action(self._gateway_id, "Quickupdate")
        await self._client.wait_for_gateway_actions_idle(self._gateway_id)
        await self._apply_snapshot()
        await self.controller.notify_scan_complete(set(self.controller.get_modules()))

    async def send(self, msg: Message) -> None:
        """Translate and send a Velbus message through the manager."""
        await self._translator.send(msg)

    async def sync_clock(self, dt: datetime.datetime | None = None) -> None:
        """Signum Manager does not expose bus clock sync."""
        raise VelbusNotSupported("Clock sync")

    def schedule_reconnect(self) -> None:
        """WebSocket client reconnects automatically; nothing to schedule."""

    async def wait_on_all_messages_sent_async(self) -> None:
        """Manager commands are synchronous REST calls; no outbound queue."""

    async def set_memo_text(self, address: int, text: str) -> None:
        """Send memo text through the manager SetMemoText action."""
        thing_id = self.module_thing_id(address)
        if thing_id is None:
            return
        await self._client.invoke_action(thing_id, "SetMemoText", {"MemoText": text})

    async def _apply_snapshot(self) -> None:
        async with self._snapshot_lock:
            if self._gateway_id is None:
                return
            try:
                actors = await self._client.get_actors(
                    self._gateway_id, include_properties=True
                )
            except VelbusAuthenticationFailed:
                await self._fire_auth_failed()
                await self._set_manager_available(False)
                raise
            except Exception:
                _LOGGER.exception("Signum snapshot read failed")
                raise

            seen: set[int] = set()
            for actor in actors:
                if actor.get("type") != "velbusmodule":
                    continue
                addr = int(actor["mainAddress"])
                seen.add(addr)
                try:
                    module_type = manager_module_type_to_code(str(actor["moduleType"]))
                except ValueError:
                    _LOGGER.warning(
                        "Skipping unknown Signum module type %s at %s",
                        actor.get("moduleType"),
                        addr,
                    )
                    continue

                build_year, build_week = parse_build_number(actor.get("buildNumber", 0))
                serial = actor.get("serialNumber")
                if self.controller.get_module(addr) is None:
                    await self.controller.add_module(
                        addr,
                        module_type,
                        serial=serial,
                        build_year=build_year,
                        build_week=build_week,
                    )
                    sub_map: dict[int, int] = {}
                    for idx, sub in enumerate(actor.get("subAddresses", []), start=1):
                        if int(sub) != 0xFF:
                            sub_map[idx] = int(sub)
                    if sub_map:
                        module = self.controller.get_module(addr)
                        if module is not None:
                            self.controller.add_submodules(module, sub_map)

                module = self.controller.get_module(addr)
                if module is None:
                    continue
                module.set_manager_display_name(
                    actor.get("name") or module.get_type_name()
                )
                self._module_things[addr] = str(actor["id"])
                await module.load_from_manager(actor.get("channels", []))
                for ch in actor.get("channels", []):
                    channel_id = remap_channel_number(module_type, int(ch["channelId"]))
                    thing_id = str(ch["id"])
                    self._channel_things[(addr, channel_id)] = thing_id
                    self._thing_channels[thing_id] = (addr, channel_id)
                    props = ch.get("properties") or {}
                    chan = module.get_channels().get(channel_id)
                    if chan is not None and props:
                        updates = map_properties_to_update(chan, props)
                        if updates:
                            await module.apply_manager_channel_update(
                                channel_id, updates
                            )
                        if isinstance(chan, Dimmer) and props.get("Brightness"):
                            self._translator.remember_brightness(
                                addr,
                                channel_id,
                                int(props["Brightness"]),
                            )

                mod_props = actor.get("properties") or {}
                if mod_props:
                    for prop_key, values in map_module_properties(
                        module, mod_props
                    ).items():
                        await module.apply_manager_property_update(prop_key, values)

            stale = set(self.controller.get_modules()) - seen
            for address in stale:
                await self.controller.remove_stale_module(address)

    async def _on_ws_message(self, data: dict[str, Any]) -> None:
        if not self._available:
            await self._set_manager_available(True)
        msg_type = data.get("messageType")
        if msg_type == "propertyStatus":
            await self._handle_property_status(data)
        elif msg_type == "gatewayStatus":
            await self._handle_gateway_status(data)
        elif msg_type == "actorStatus":
            _LOGGER.debug("Signum actorStatus: %s", data)

    async def _handle_property_status(self, data: dict[str, Any]) -> None:
        thing_id = data.get("thingId")
        if not isinstance(thing_id, str):
            return
        payload = data.get("data") or {}
        if not isinstance(payload, dict):
            return

        if not self._bus_connected:
            self._bus_connected = True
            self._sync_bus_link_event()
            _LOGGER.info("Velbus bus link active (live Signum propertyStatus)")
            await self._notify_connection_state()

        if thing_id in self._thing_channels:
            address, channel_num = self._thing_channels[thing_id]
            module = self.controller.get_module(address)
            if module is None:
                return
            chan = module.get_channels().get(channel_num)
            if chan is None:
                return
            updates = map_properties_to_update(chan, payload)
            if updates:
                _LOGGER.debug(
                    "Signum propertyStatus %s address %s ch %s %s",
                    thing_id,
                    address,
                    channel_num,
                    updates,
                )
                await module.apply_manager_channel_update(channel_num, updates)
            if "Brightness" in payload:
                self._translator.remember_brightness(
                    address, channel_num, int(payload["Brightness"])
                )
            return

        for addr, mod_id in self._module_things.items():
            if mod_id != thing_id:
                continue
            module = self.controller.get_module(addr)
            if module is None:
                return
            for prop_key, values in map_module_properties(module, payload).items():
                await module.apply_manager_property_update(prop_key, values)
            return

    async def _handle_gateway_status(self, data: dict[str, Any]) -> None:
        state = (data.get("data") or {}).get("state")
        link = _gateway_link_up(state)
        if link is None:
            return
        if link == self._bus_connected:
            return
        self._bus_connected = link
        self._sync_bus_link_event()
        if not link:
            if not self._logged_bus_unavailable:
                _LOGGER.info("Velbus bus link unavailable (Signum Manager)")
                self._logged_bus_unavailable = True
        else:
            if self._logged_bus_unavailable:
                _LOGGER.info("Velbus bus link available again (Signum Manager)")
            self._logged_bus_unavailable = False
        await self._notify_connection_state()

    async def _on_ws_disconnect(self) -> None:
        await self._set_manager_available(False)

    async def _set_manager_available(self, available: bool) -> None:
        if available == self._available:
            return
        self._available = available
        if not available:
            if not self._logged_manager_unavailable:
                _LOGGER.info("Signum Manager unavailable")
                self._logged_manager_unavailable = True
        else:
            if self._logged_manager_unavailable:
                _LOGGER.info("Signum Manager available again")
            self._logged_manager_unavailable = False
        await self._notify_connection_state()
        if available and self.controller.get_modules():
            try:
                await self._apply_snapshot()
            except VelbusAuthenticationFailed:
                await self._fire_auth_failed()

    async def _notify_connection_state(self) -> None:
        await self.controller.notify_connection_state(self.is_connected)

    async def _fire_auth_failed(self) -> None:
        for callback in list(self._auth_failed_callbacks):
            result = callback()
            if asyncio.iscoroutine(result):
                await result
