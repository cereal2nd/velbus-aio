"""Main interface for the velbusaio lib."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import datetime
import itertools
import logging
import pathlib
import typing as t
from urllib.parse import urlparse

from aiohttp import ClientSession
import anyio

from velbusaio.bus.base import VelbusBusBackend
from velbusaio.bus.manager.backend import ManagerBackend
from velbusaio.bus.raw.backend import RawBusBackend
from velbusaio.channels import (
    Blind,
    Button,
    ButtonCounter,
    Channel,
    Dimmer,
    Relay,
    SensorNumber,
    Temperature,
)
from velbusaio.config import ConfigParameter
from velbusaio.exceptions import VelbusConnectionFailed
from velbusaio.handler import PacketHandler
from velbusaio.helpers import get_cache_dir
from velbusaio.message import Message
from velbusaio.messages.module_type_request import ModuleTypeRequestMessage
from velbusaio.module import Module
from velbusaio.properties import LightValue, SelectedProgram
from velbusaio.raw_message import RawMessage


@dataclass
class ScheduledTask:
    """A scheduled task that runs at a specific interval."""

    name: str
    callback: Callable[[], Awaitable[None]]
    interval_seconds: float
    _task: asyncio.Task[None] | None = None
    _running: bool = False

    async def _run_loop(self) -> None:
        """Run the task in a loop."""
        self._running = True
        while self._running:
            try:
                await asyncio.sleep(self.interval_seconds)
                await self.callback()
            except asyncio.CancelledError:
                break
            except (RuntimeError, ValueError, TypeError, AttributeError):
                logging.getLogger("velbus-scheduler").exception(
                    "Error in scheduled task '%s'", self.name
                )

    def start(self) -> None:
        """Start the scheduled task."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_loop())

    def stop(self) -> None:
        """Stop the scheduled task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()


class Velbus:
    """A velbus controller."""

    def __init__(
        self,
        dsn: str,
        cache_dir: str = get_cache_dir(),
        vlp_file: str | None = None,
        one_address: int | None = None,
        session: ClientSession | None = None,
        access_token: str | None = None,
        *,
        gateway_id: str | None = None,
    ) -> None:
        """Init the Velbus controller, optionally bound to a Manager gateway ID."""
        self._log = logging.getLogger("velbus")
        self._closing = False
        self._auto_reconnect = True

        self._destination = dsn
        self._handler = PacketHandler(self, one_address)
        self._modules: dict[int, Module] = {}
        self._submodules: list[int] = []
        self._vlp_file = vlp_file
        self._cache_dir: str = cache_dir
        self._on_connect_callbacks: list[t.Callable[[], Awaitable[None]]] = []
        self._on_disconnect_callbacks: list[t.Callable[[], Awaitable[None]]] = []
        self._on_module_found_callbacks: list[
            t.Callable[[Module], Awaitable[None]]
        ] = []
        self._on_scan_complete_callbacks: list[
            t.Callable[[set[int]], Awaitable[None]]
        ] = []
        self._background_tasks: set[asyncio.Task[object]] = set()
        self._scheduled_tasks: dict[str, ScheduledTask] = {}
        self._scheduler_log = logging.getLogger("velbus-scheduler")
        self._had_modules_before_connect = False

        parts = urlparse(dsn)
        if parts.scheme == "manager":
            if parts.hostname is None or parts.port is None:
                raise VelbusConnectionFailed
            self._backend: VelbusBusBackend = ManagerBackend(
                self,
                parts.hostname,
                parts.port,
                session,
                access_token,
                gateway_id=gateway_id,
            )
        else:
            if gateway_id is not None:
                raise ValueError("gateway_id requires a manager:// DSN")
            self._backend = RawBusBackend(self, dsn)

    @property
    def manager_backend(self) -> ManagerBackend | None:
        """Return the Signum Manager backend when active."""
        if isinstance(self._backend, ManagerBackend):
            return self._backend
        return None

    @property
    def raw_backend(self) -> RawBusBackend | None:
        """Return the raw protocol backend when active."""
        if isinstance(self._backend, RawBusBackend):
            return self._backend
        return None

    def add_auth_failed_callback(self, meth: t.Callable[[], Awaitable[None]]) -> None:
        """Register a coroutine when Signum Manager rejects the access token."""
        self._backend.add_auth_failed_callback(meth)

    def remove_auth_failed_callback(
        self, meth: t.Callable[[], Awaitable[None]]
    ) -> None:
        """Remove a previously registered auth-failed coroutine."""
        self._backend.remove_auth_failed_callback(meth)

    def add_background_task(self, task: asyncio.Task[object]) -> None:
        """Keep a background task referenced until it completes."""
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def add_connect_callback(self, meth: t.Callable[[], Awaitable[None]]) -> None:
        """Register a coroutine to be called on connect."""
        self._on_connect_callbacks.append(meth)

    def remove_connect_callback(self, meth: t.Callable[[], Awaitable[None]]) -> None:
        """Remove a previously registered on connect coroutine."""
        self._on_connect_callbacks.remove(meth)

    def add_disconnect_callback(self, meth: t.Callable[[], Awaitable[None]]) -> None:
        """Register a coroutine to be called on disconnect."""
        self._on_disconnect_callbacks.append(meth)

    def remove_disconnect_callback(self, meth: t.Callable[[], Awaitable[None]]) -> None:
        """Remove a previously registered on disconnect coroutine."""
        self._on_disconnect_callbacks.remove(meth)

    def add_module_found_callback(
        self, meth: t.Callable[[Module], Awaitable[None]]
    ) -> None:
        """Register a coroutine to be called on module found."""
        self._on_module_found_callbacks.append(meth)

    def remove_module_found_callback(
        self, meth: t.Callable[[Module], Awaitable[None]]
    ) -> None:
        """Remove a previously registered on module found coroutine."""
        self._on_module_found_callbacks.remove(meth)

    def add_scan_complete_callback(
        self, meth: t.Callable[[set[int]], Awaitable[None]]
    ) -> None:
        """Register a coroutine called after a full bus module scan."""
        self._on_scan_complete_callbacks.append(meth)

    def remove_scan_complete_callback(
        self, meth: t.Callable[[set[int]], Awaitable[None]]
    ) -> None:
        """Remove a previously registered scan-complete coroutine."""
        self._on_scan_complete_callbacks.remove(meth)

    async def _on_modules_loaded(self, module: Module) -> None:
        """Called when all modules are loaded."""
        for callback in self._on_module_found_callbacks:
            await callback(module)

    async def notify_scan_complete(self, found_addresses: set[int]) -> None:
        """Notify listeners that a full bus scan finished."""
        for callback in self._on_scan_complete_callbacks:
            await callback(found_addresses)

    async def remove_stale_module(self, address: int) -> None:
        """Drop a module that did not respond during a full bus scan."""
        module = self._modules.pop(address, None)
        if module is None:
            return
        for sub_addr in module.get_addresses():
            if sub_addr == address:
                continue
            if sub_addr in self._submodules:
                self._submodules.remove(sub_addr)
        if self.manager_backend is None:
            cache_file = pathlib.Path(self._cache_dir) / f"{address}.json"
            if await anyio.Path(cache_file).is_file():
                await anyio.Path(cache_file).unlink()
        self._log.info("Removed stale module at address %s (%#02x)", address, address)

    @property
    def connected(self) -> bool:
        """Return connection state."""
        return self._backend.is_connected

    @property
    def closing(self) -> bool:
        """Return whether :meth:`stop` has been requested."""
        return self._closing

    @property
    def auto_reconnect_enabled(self) -> bool:
        """Return whether the transport should reconnect after a drop."""
        return self._auto_reconnect

    @property
    def vlp_file(self) -> str | None:
        """Return the optional VLP file used instead of a live bus scan."""
        return self._vlp_file

    @property
    def log(self) -> logging.Logger:
        """Return the controller logger."""
        return self._log

    @property
    def packet_handler(self) -> PacketHandler:
        """Return the inbound packet handler."""
        return self._handler

    def is_closing(self) -> bool:
        """Return whether shutdown is in progress."""
        return self._closing

    async def notify_connection_state(self, is_connected: bool) -> None:
        """Notify listeners that the transport link changed."""
        await self._on_connection_state(is_connected)

    async def deliver_message(self, msg: RawMessage) -> None:
        """Deliver an inbound raw packet to the handler."""
        await self._on_message_received(msg)

    async def _on_connection_state(self, is_connected: bool) -> None:
        """Respond to transport connection state changes."""
        if is_connected:
            if self._had_modules_before_connect:
                self._invalidate_all_memory_caches()
            self._had_modules_before_connect = bool(self._modules)
            for callback in self._on_connect_callbacks:
                await callback()
        else:
            self._had_modules_before_connect = bool(self._modules)
            for callback in self._on_disconnect_callbacks:
                await callback()
            if self._auto_reconnect and not self._closing:
                self._backend.schedule_reconnect()
        for mod in self._modules.values():
            for chan in mod.get_channels().values():
                await chan.status_update()

    def _invalidate_all_memory_caches(self) -> None:
        """Drop EEPROM caches for every known module."""
        for module in self._modules.values():
            module.invalidate_config_memory_cache()

    def get_cache_dir(self) -> str:
        """Return the cache directory."""
        return self._cache_dir

    async def _on_message_received(self, msg: RawMessage) -> None:
        """On message received function."""
        await self._handler.handle(msg)

    async def add_module(
        self,
        addr: int,
        typ: int,
        serial: int | str | None = None,
        memorymap: int | str | None = None,
        build_year: int | None = None,
        build_week: int | None = None,
    ) -> None:
        """Add a found module to the module cache."""
        module = Module.factory(
            addr,
            typ,
            serial=serial,
            build_year=build_year,
            build_week=build_week,
            memorymap=memorymap,
            cache_dir=self._cache_dir,
            on_module_found=self._on_modules_loaded,
        )
        await module.initialize(self.send, self)
        self._modules[addr] = module
        self._log.info(f"Found module {addr}: {module}")

    def add_submodules(self, module: Module, subList: dict[int, int]) -> None:
        """Add submodules address to module."""
        for sub_num, sub_addr in subList.items():
            if sub_addr == 0xFF:
                continue
            self._submodules.append(sub_addr)
            module.add_subaddress(sub_num, sub_addr)
        module.cleanupSubChannels()

    def addr_is_submodule(self, addr: int) -> bool:
        """Check if an address is a submodule."""
        return addr in self._submodules

    def get_modules(self) -> dict[int, Module]:
        """Return the module cache."""
        return self._modules

    def get_module(self, addr: int) -> None | Module:
        """Get a module on an address."""
        if addr in self._modules:
            return self._modules[addr]
        for module in self._modules.values():
            if addr in module.get_addresses():
                return module
        return None

    def get_channels(self, addr: int) -> dict[int, Channel] | None:
        """Get the channels for an address."""
        if addr in self._modules:
            return (self._modules[addr]).get_channels()
        return None

    async def stop(self) -> None:
        """Stop the controller."""
        self._closing = True
        self._auto_reconnect = False
        await self._backend.stop()
        if isinstance(self._backend, RawBusBackend):
            for scheduled in self._scheduled_tasks.values():
                scheduled.stop()
            for bg_task in list(self._background_tasks):
                if not bg_task.done():
                    bg_task.cancel()
            if self._background_tasks:
                await asyncio.gather(
                    *list(self._background_tasks), return_exceptions=True
                )
            self._background_tasks.clear()

    async def connect(self) -> None:
        """Connect to the bus and load all the data."""
        self._closing = False
        self._auto_reconnect = True
        await self._handler.read_protocol_data()
        if self.is_closing():
            return
        await self._backend.connect()

    async def start(self) -> None:
        """Start the controller."""
        await anyio.Path(self._cache_dir).mkdir(parents=True, exist_ok=True)
        await self._backend.start()

    async def scan(self) -> None:
        """Service endpoint to restart the scan."""
        await self._backend.scan()

    async def sendTypeRequestMessage(self, address: int) -> None:
        """Send a module type request message."""
        msg = ModuleTypeRequestMessage(address)
        await self.send(msg)

    async def send(self, msg: Message) -> None:
        """Send a packet."""
        await self._backend.send(msg)

    def get_all_sensor(
        self,
    ) -> list[ButtonCounter | Temperature | LightValue | SensorNumber]:
        """Get all sensors."""
        return self._get_all("sensor")

    def get_all_switch(self) -> list[Relay]:
        """Get all switches."""
        return self._get_all("switch")

    def get_all_binary_sensor(self) -> list[Button]:
        """Get all binary sensors."""
        return self._get_all("binary_sensor")

    def get_all_button(self) -> list[Button | ButtonCounter]:
        """Get all buttons."""
        return self._get_all("button")

    def get_all_climate(self) -> list[Temperature]:
        """Get all climate devices."""
        return self._get_all("climate")

    def get_all_temp_config(self) -> list[Temperature]:
        """Get temperature channels that expose settings configuration."""
        result: list[Temperature] = []
        seen: set[tuple[int, int]] = set()
        for channel in itertools.chain(self.get_all_climate(), self.get_all_sensor()):
            if not isinstance(channel, Temperature):
                continue
            if channel.get_temp_settings() is None:
                continue
            key = (channel.get_module_address(), channel.get_channel_number())
            if key in seen:
                continue
            seen.add(key)
            result.append(channel)
        return result

    def get_all_cover(self) -> list[Blind]:
        """Get all covers."""
        return self._get_all("cover")

    def get_all_select(self) -> list[SelectedProgram]:
        """Get all select devices."""
        return self._get_all("select")

    def get_all_light(self) -> list[Dimmer]:
        """Get all light devices."""
        return self._get_all("light")

    def get_all_led(self) -> list[Button]:
        """Get all LED devices."""
        return self._get_all("led")

    def get_all_relay_config(self) -> list[Relay]:
        """Get relay channels that expose configuration parameters."""
        return [
            channel
            for channel in self.get_all_switch()
            if hasattr(channel, "get_config_parameters")
        ]

    def get_all_config_parameters(self) -> list[ConfigParameter]:
        """Get CONFIG parameters that should be exposed as Home Assistant entities."""
        params: list[ConfigParameter] = []
        for channel in self.get_all_relay_config():
            params.extend(
                param for param in channel.get_config_parameters() if param.entity
            )
        seen: set[tuple[int, int | None, str]] = set()
        for temp_channel in self.get_all_temp_config():
            for param in temp_channel.get_config_parameters():
                if not param.entity:
                    continue
                key = (
                    temp_channel.get_module_address(),
                    param.channel,
                    param.key,
                )
                if key in seen:
                    continue
                seen.add(key)
                params.append(param)
        return params

    def _get_all(self, class_name: str) -> list[t.Any]:
        """Get all channels."""
        return [
            chan
            for addr, mod in (self.get_modules()).items()
            if addr not in self._submodules
            for chan in itertools.chain(
                (mod.get_channels()).values(), (mod.get_properties()).values()
            )
            if class_name in chan.get_categories()
        ]

    async def sync_clock(self, dt: datetime.datetime | None = None) -> None:
        """Will send all the needed messages to sync the clock."""
        await self._backend.sync_clock(dt)

    async def wait_on_all_messages_sent_async(self) -> None:
        """Wait for all messages to be sent."""
        await self._backend.wait_on_all_messages_sent_async()

    def add_scheduled_task(
        self,
        name: str,
        callback: Callable[[], Awaitable[None]],
        interval_seconds: float,
    ) -> None:
        """Add a scheduled task that runs at a specific interval."""
        if name in self._scheduled_tasks:
            self._scheduler_log.warning(f"Task '{name}' already exists, replacing it")
            self.remove_scheduled_task(name)

        task = ScheduledTask(
            name=name,
            callback=callback,
            interval_seconds=interval_seconds,
        )
        self._scheduled_tasks[name] = task
        task.start()
        self._scheduler_log.info(
            f"Scheduled task '{name}' added (interval: {interval_seconds}s)"
        )

    def remove_scheduled_task(self, name: str) -> None:
        """Remove a scheduled task."""
        if name in self._scheduled_tasks:
            self._scheduled_tasks[name].stop()
            del self._scheduled_tasks[name]
            self._scheduler_log.info(f"Scheduled task '{name}' removed")

    def get_scheduled_tasks(self) -> dict[str, ScheduledTask]:
        """Get all scheduled tasks."""
        return self._scheduled_tasks.copy()
