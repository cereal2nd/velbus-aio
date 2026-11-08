"""This represents a velbus module."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import importlib.resources
import json
import logging
from typing import TYPE_CHECKING, Any

import anyio

if TYPE_CHECKING:
    from velbusaio.controller import Velbus as Controller

from velbusaio import properties as properties_module
from velbusaio.actions import (
    ActionSlot,
    ActionTable,
    build_action_tables,
    reserved_ranges,
)
from velbusaio.channels import Channel, Dimmer, Temperature as TemperatureChannelType
from velbusaio.command_registry import commandRegistry, instantiate_command
from velbusaio.config import decode_name, encode_name
from velbusaio.const import PRIORITY_LOW, SCAN_MODULEINFO_TIMEOUT_INITIAL
from velbusaio.helpers import h2
from velbusaio.memory import MemoryBackend
from velbusaio.memory_prefetch import MemoryAccessCoordinator
from velbusaio.message import Message
from velbusaio.messages.channel_name_request import (
    COMMAND_CODE as CHANNEL_NAME_REQUEST_COMMAND_CODE,
)
from velbusaio.messages.clear_led import ClearLedMessage
from velbusaio.messages.dali_device_settings import (
    DaliDeviceSettingMsg,
    DeviceType as DaliDeviceType,
    DeviceTypeMsg as DaliDeviceTypeMsg,
    MemberOfGroupMsg,
)
from velbusaio.messages.dali_device_settings_request import (
    COMMAND_CODE as DALI_DEVICE_SETTINGS_REQUEST_COMMAND_CODE,
)
from velbusaio.messages.dali_dim_value_status import DimValueStatus
from velbusaio.messages.fast_blinking_led import FastBlinkingLedMessage
from velbusaio.messages.push_button_status import PushButtonStatusMessage
from velbusaio.messages.set_led import SetLedMessage
from velbusaio.messages.slow_blinking_led import SlowBlinkingLedMessage
from velbusaio.module_handlers import ModuleMessageHandlersMixin
from velbusaio.module_scan import ModuleScanMixin, _coerce_cached_sub_address
from velbusaio.properties import Property
from velbusaio.temp_settings import TemperatureSettings, build_temperature_settings


class Module(ModuleMessageHandlersMixin, ModuleScanMixin):
    """Abstract class for Velbus hardware modules."""

    @classmethod
    def factory(
        cls,
        module_address: int,
        module_type: int,
        serial: int | str | None = None,
        memorymap: int | str | None = None,
        build_year: int | None = None,
        build_week: int | None = None,
        cache_dir: str | None = None,
        on_module_found: Callable[[Module], Awaitable[None]] | None = None,
    ) -> Module:
        """Module factory method."""
        if module_type in {0x45, 0x5A}:
            return VmbDali(
                module_address,
                module_type,
                serial,
                memorymap,
                build_year,
                build_week,
                cache_dir,
                on_module_found,
            )

        return Module(
            module_address,
            module_type,
            serial,
            memorymap,
            build_year,
            build_week,
            cache_dir,
            on_module_found,
        )

    def __init__(
        self,
        module_address: int,
        module_type: int,
        serial: int | str | None = None,
        memorymap: int | str | None = None,
        build_year: int | None = None,
        build_week: int | None = None,
        cache_dir: str | None = None,
        on_module_found: Callable[[Module], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize Module object."""
        self._address = module_address
        self._type = int(module_type)
        self._data: dict[str, Any] = {}

        self._name: str | dict[Any, Any] | None = None
        self._name_buffer: dict[
            int, str
        ] = {}  # temporary buffer while assembling name from memory blocks
        self._sub_address: dict[int, int] = {}
        # the bus reports the serial as an int, a vlp file as a str => normalize
        self.serial = str(serial) if serial is not None else None
        self.memory_map_version = memorymap
        self.build_year = build_year
        self.build_week = build_week
        # Set when the module's firmware predates the memory map its spec
        # describes. Home Assistant surfaces this, and writes are refused.
        self._memory_map_outdated = False
        self._cache_dir = cache_dir
        self._is_loading = False
        self._got_status = asyncio.Event()
        self._got_status.clear()
        self._channels: dict[int, Channel] = {}
        self._properties: dict[str, Property] = {}
        self._memory: MemoryBackend | None = None
        self._action_tables: dict[int, ActionTable] = {}
        self._temp_settings: TemperatureSettings | None = None
        self.loaded = False
        self._use_cache = True
        self._loaded_cache: dict[str, Any] = {}
        self._panel_metadata_ready = False
        # serialize cache writes for this module to avoid concurrent
        # coroutines interleaving writes to the same file
        self._cache_lock = asyncio.Lock()
        self._on_module_found: Callable[[Module], Awaitable[None]] | None = (
            on_module_found
        )

    async def wait_for_status_messages(self) -> None:
        """Wait for status messages to be received."""
        try:
            await asyncio.wait_for(self._got_status.wait(), 2)
        except TimeoutError:
            self._log.warning(f"Timeout waiting for status messages for: {self}")

    def get_initial_timeout(self) -> int:
        """Get initial timeout for scanning module info."""
        return SCAN_MODULEINFO_TIMEOUT_INITIAL

    async def initialize(
        self, writer: Callable[[Message], Awaitable[None]], controller: Controller
    ) -> None:
        """Initialize the module."""
        self._controller = controller
        self._log = logging.getLogger("velbus-module")

        # Build message handler dispatch table
        self._message_handlers = self._build_message_handlers()

        # load the protocol data
        try:
            # Load global.json first
            global_data = {}
            try:
                with importlib.resources.path(
                    __name__, "module_spec/global.json"
                ) as fspath:
                    async with await anyio.open_file(fspath) as global_file:
                        global_data = json.loads(await global_file.read())
                self._log.debug("Global module spec loaded")
            except FileNotFoundError:
                self._log.debug("No global module spec found")

            # Load module-specific data
            with importlib.resources.path(
                __name__, f"module_spec/{h2(self._type)}.json"
            ) as fspath:
                async with await anyio.open_file(fspath) as protocol_file:
                    self._data = json.loads(await protocol_file.read())

            # Merge global data into module data (module-specific takes precedence)
            for key, value in global_data.items():
                if key not in self._data:
                    self._data[key] = value
                elif isinstance(value, dict) and isinstance(self._data[key], dict):
                    # Deep merge for nested dictionaries
                    self._data[key] = {**value, **self._data[key]}

            self._log.debug(f"Module spec {h2(self._type)} loaded")
        except FileNotFoundError:
            self._log.warning(f"No module spec for {h2(self._type)}")
            self._data = {}
            for key, value in global_data.items():
                if key not in self._data:
                    self._data[key] = value
                elif isinstance(value, dict) and isinstance(self._data[key], dict):
                    self._data[key] = {**value, **self._data[key]}

        self._check_memory_map_build()

        commandRegistry.register_module_commands(
            self._type, self._data.get("CommandToClass", {})
        )

        # set some params from the velbus controller
        self._writer = writer
        get_coordinator = getattr(controller, "get_memory_access_coordinator", None)
        access_coordinator = get_coordinator() if get_coordinator else None
        self._memory = MemoryBackend(
            self._address,
            writer,
            self._log,
            access_coordinator=access_coordinator,
        )
        if self._memory_map_outdated:
            self._memory.block_writes(
                f"module build {self.get_build()} predates the memory map from "
                f"build {self.get_memory_map_build()} that its spec describes"
            )
        memory_spec = self._data.get("Memory", {})
        self._action_tables = build_action_tables(
            self._memory,
            memory_spec.get("ActionTable", {}),
            self._log,
            reserved=reserved_ranges(memory_spec),
        )
        temp_chan: int | None = None
        if "TemperatureChannel" in self._data:
            temp_chan = self._translate_channel_name(self._data["TemperatureChannel"])
        self._temp_settings = build_temperature_settings(
            self._address,
            writer,
            self._data,
            channel=temp_chan,
            logger=self._log,
        )
        for chan in self._channels.values():
            chan.set_writer(writer)

    def get_build(self) -> str | None:
        """Return the firmware build as "YYWW", or None when unknown."""
        if self.build_year is None or self.build_week is None:
            return None
        return f"{self.build_year:02d}{self.build_week:02d}"

    def get_memory_map_build(self) -> str | None:
        """Return the build from which this spec's memory map applies."""
        return self._data.get("MemoryMapBuild")

    def is_memory_map_outdated(self) -> bool:
        """Whether the module predates the memory map its spec describes.

        When true the spec's addresses do not match this module's eeprom,
        so its memory must not be written. Home Assistant surfaces this so
        the mismatch is visible instead of silently corrupting data.
        """
        return self._memory_map_outdated

    def _check_memory_map_build(self) -> None:
        """Determine whether the module predates its spec's memory map.

        Modules report their firmware build as year and week. The protocol
        documents state the build from which each memory map applies, and
        MemoryMapBuild records the one this spec was written against. A
        module older than that runs an earlier layout, so every address in
        the spec is suspect: reading a name or an action table returns
        whatever else lives there, and writing destroys it.
        """
        self._memory_map_outdated = False
        expected = self.get_memory_map_build()
        reported = self.get_build()
        if expected is None or reported is None:
            return
        # "YYWW", the same shape vlp_reader compares build numbers in.
        if len(reported) != len(expected):
            self._log.debug(f"Cannot compare build {reported} to {expected}")
            return
        if reported >= expected:
            return

        self._memory_map_outdated = True
        self._log.warning(
            f"Module {self._address} ({h2(self._type)}) reports build "
            f"{reported}, but the module spec describes the memory map from "
            f"build {expected} onwards. Memory addresses may be wrong; names "
            f"and action tables read from this module can be incorrect, so "
            f"writing to its memory is refused."
        )

    def cleanupSubChannels(self) -> None:
        """Cleanup subchannels that are not defined."""
        # TODO: 21/11/2022 DannyDeGaspari: Fix needed
        # Care should be taken for this function, not all subaddresses have their channels on multiples of 8.
        # The last subaddress contain typically the temperature channels, has more then 8 channels
        # and doesn't start on a boundary of 8.
        # E.g. The VMBGP4 has one subaddress, so since the second subaddress is not defined,
        # this function will delete channels 17-24 while 17 and 18 belong to the temperature channels.
        #
        # The solution would be that this functions knows were the temperature channels are located
        # and/or what the max number of subaddresses are for each module.
        # if self._sub_address == {} and self.loaded:
        #   raise Exception("No subaddresses defined")
        for sub in range(1, 4):
            if sub not in self._sub_address:
                for i in range(((sub * 8) + 1), (((sub + 1) * 8) + 1)):
                    if i in self._channels and not isinstance(
                        self._channels[i], TemperatureChannelType
                    ):
                        del self._channels[i]

    def get_address(self) -> int:
        """Get the module address."""
        return self._address

    def get_addresses(self) -> list[int]:
        """Get all addresses for this module."""
        res = [self._address]
        res.extend(self._sub_address.values())
        return res

    def get_sub_address_dict(self) -> dict[int, int]:
        """Return the sub addresses dict."""
        return self._sub_address

    def is_channel_active(self, channel_num: int) -> bool:
        """Check if a channel is active based on sub-address configuration."""
        # Channels 1-8 are always on the master address (active)
        if channel_num <= 8:
            return True

        # Calculate sub-address index (1, 2, 3...)
        # Block 1: 1-8 (index 0 / master)
        # Block 2: 9-16 (index 1)
        # Block 3: 17-24 (index 2)
        # Block 4: 25-32 (index 3)
        sub_idx = (channel_num - 1) // 8

        # Check if this sub-index exists in the active sub-addresses
        return sub_idx in self._sub_address

    def add_subaddress(self, num: int, addr: int) -> None:
        """Add a subaddress to this module."""
        self._sub_address[num] = addr

    def get_type(self) -> int:
        """Get the module type."""
        return self._type

    def get_type_name(self) -> str:
        """Get the module type name."""
        module_type = self._data.get("Type")
        if isinstance(module_type, str):
            return module_type
        return "UNKNOWN"

    def get_serial(self) -> str | None:
        """Get the module serial number."""
        return self.serial

    def get_name(self) -> str:
        """Get the module name."""
        if isinstance(self._name, str):
            return self._name
        return ""

    def get_sw_version(self) -> str:
        """Get the module software version."""
        return f"{self.build_year}.{self.build_week}"

    def calc_channel_offset(self, address: int) -> int:
        """Calculate channel offset based on address."""
        _channel_offset = 0
        if self._address != address:
            for _sub_addr_key, _sub_addr_val in self._sub_address.items():
                if _sub_addr_val == address:
                    _channel_offset = 8 * _sub_addr_key
                    break
        return _channel_offset

    def on_connect(self, meth: Callable[[], Awaitable[None]]) -> None:
        """Register a coroutine to be called on connect."""
        self._controller.add_connect_callback(meth)

    def remove_on_connect(self, meth: Callable[[], Awaitable[None]]) -> None:
        """Remove a previously registered on connect coroutine."""
        self._controller.remove_connect_callback(meth)

    def on_disconnect(self, meth: Callable[[], Awaitable[None]]) -> None:
        """Register a coroutine to be called on disconnect."""
        self._controller.add_disconnect_callback(meth)

    def remove_on_disconnect(self, meth: Callable[[], Awaitable[None]]) -> None:
        """Remove a previously registered on disconnect coroutine."""
        self._controller.remove_disconnect_callback(meth)

    @property
    def is_connected(self) -> bool:
        """Return if the module is connected."""
        return self._controller.connected

    def get_channels(self) -> dict[int, Channel]:
        """List all channels for this module."""
        return self._channels

    def get_properties(self) -> dict[str, Property]:
        """List all properties for this module."""
        return self._properties

    def get_memory(self) -> MemoryBackend | None:
        """Return the module memory backend, if initialized."""
        return self._memory

    def get_action_table(self, channel: int) -> ActionTable | None:
        """Return the action table for a channel, if this module has one."""
        return self._action_tables.get(channel)

    def get_action_tables(self) -> dict[int, ActionTable]:
        """Return all action tables for this module."""
        return dict(self._action_tables)

    def get_channel_enable_spec(self, channel: int) -> dict[str, int] | None:
        """Return EEPROM enable/disable metadata for a channel, if supported."""
        spec = self._data.get("Memory", {}).get("ChannelEnable")
        if not spec:
            return None
        address = spec.get("channels", {}).get(f"{channel:02d}")
        if address is None:
            return None
        return {
            "address": int(str(address), 16),
            "disabled_value": int(spec.get("disabled_value", 0xFF)),
            "enabled_value": int(spec.get("enabled_value", 0x01)),
        }

    def get_temp_settings(self) -> TemperatureSettings | None:
        """Return the temperature settings helper, if this module supports it."""
        return self._temp_settings

    async def load_action_table(
        self, channel: int, *, force: bool = False
    ) -> list[ActionSlot]:
        """Load (or reload) the action table for a channel."""
        table = self.get_action_table(channel)
        if table is None:
            return []
        return await table.load(force=force)

    def invalidate_config_memory_cache(self) -> None:
        """Drop EEPROM and decoded config-panel caches for this module."""
        self._panel_metadata_ready = False
        if self._memory is not None:
            self._memory.invalidate()
        cleared_shared: set[int] = set()
        for table in self._action_tables.values():
            table.clear_decoded_cache()
            shared = table.shared_store
            if shared is not None and id(shared) not in cleared_shared:
                shared.slots = None
                cleared_shared.add(id(shared))

    def is_panel_metadata_ready(self) -> bool:
        """Return True when panel metadata EEPROM is in the shadow cache."""
        return self._panel_metadata_ready

    def _needs_panel_metadata_cache(self) -> bool:
        memory_spec = self._data.get("Memory", {})
        has_noc = any(
            table.noc_address is not None for table in self._action_tables.values()
        )
        return bool(memory_spec.get("ChannelEnable") or has_noc)

    async def ensure_panel_metadata_cache(self) -> None:
        """Load enable/contact EEPROM for module/get without action tables."""
        if self._panel_metadata_ready:
            return
        if self._memory is None or not self._needs_panel_metadata_cache():
            self._panel_metadata_ready = True
            return

        enable_spec = self._data.get("Memory", {}).get("ChannelEnable")
        if enable_spec:
            for address in enable_spec.get("channels", {}).values():
                await self._memory.read_byte(int(str(address), 16), use_cache=True)

        for table in self._action_tables.values():
            if table.noc_address is not None:
                await table.load_noc()
        self._panel_metadata_ready = True

    async def ensure_action_table_cache(self, channel: int) -> None:
        """Load one channel's action table into the shadow cache."""
        table = self.get_action_table(channel)
        if table is None or table.loaded:
            return
        if table.decode_from_cache():
            return
        await table.load(force=False)

    async def get_channel_actions(
        self,
        channel: int,
        *,
        refresh: bool = False,
        include_empty: bool = False,
    ) -> list[ActionSlot]:
        """Return action-table slots for the config panel."""
        if refresh:
            table = self.get_action_table(channel)
            if table is None:
                return []
            return await table.get_actions(refresh=True, include_empty=include_empty)
        await self.ensure_action_table_cache(channel)
        table = self.get_action_table(channel)
        if table is None:
            return []
        return await table.get_actions(refresh=False, include_empty=include_empty)

    async def prefetch_config_memory(
        self, coordinator: MemoryAccessCoordinator
    ) -> None:
        """Prefetch panel-relevant EEPROM into the in-process cache."""
        if self._memory is None:
            self._panel_metadata_ready = True
            return
        seen_shared_banks: set[int] = set()
        for table in self._action_tables.values():
            await coordinator.wait_prefetch_allowed()
            if table.layout == "shared" and table.bank in seen_shared_banks:
                await table.load_noc(prefetch=True)
                continue
            if table.layout == "shared":
                seen_shared_banks.add(table.bank)
            await table.load(force=False, prefetch=True)

        enable_spec = self._data.get("Memory", {}).get("ChannelEnable")
        if enable_spec:
            for address in enable_spec.get("channels", {}).values():
                await coordinator.wait_prefetch_allowed()
                await self._memory.read_byte(
                    int(str(address), 16), use_cache=True, prefetch=True
                )
        self._panel_metadata_ready = True

    def _channel_name_range(self, channel: int) -> tuple[int, int] | None:
        """Return (start, length) for a channel name memory range."""
        memory = self._data.get("Memory", {})
        channels = memory.get("Channels", {})
        key = f"{channel:02d}"
        if key not in channels:
            return None
        start_str, end_str = str(channels[key]).split("-")
        start = int(start_str, 16)
        end = int(end_str, 16)
        return start, end - start + 1

    async def set_channel_name_persistent(self, channel: int, name: str) -> None:
        """Write a channel name into module EEPROM and update the local name."""
        if self._memory is None:
            raise RuntimeError("Module memory backend is not initialized")
        name_range = self._channel_name_range(channel)
        if name_range is None:
            raise ValueError(f"Channel {channel} has no name memory range")
        start, length = name_range
        await self._memory.write_bytes(start, encode_name(name, length))
        if channel in self._channels:
            self._channels[channel].set_name(decode_name(encode_name(name, length)))
            await self._cache()

    def _load(self) -> None:
        """Method for per module type loading."""

    def number_of_channels(self) -> int:
        """Retrieve the number of available channels in this module.

        :return: int
        """
        if not len(self._channels):
            return 0
        return max(self._channels.keys())

    async def set_memo_text(self, txt: str) -> None:
        """Set memo text property."""
        memo_prop = self._properties.get("memo_text")
        if not isinstance(memo_prop, properties_module.MemoText):
            return
        await memo_prop.set(txt)

    async def __load_memory(self) -> None:
        """Request all needed memory addresses (name mangling preserved for tests)."""
        await self._load_memory_eeprom()


class VmbDali(Module):
    """DALI has a variable number of channels.

    Therefore we create a module that first creates 64 placeholder channels.
    After that it requests the DALI device settings to determine the actual channels.
    """

    def __init__(
        self,
        module_address: int,
        module_type: int,
        serial: int | str | None = None,
        memorymap: int | str | None = None,
        build_year: int | None = None,
        build_week: int | None = None,
        cache_dir: str | None = None,
        on_load_finished: Callable[[Module], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize DALI module."""
        super().__init__(
            module_address,
            module_type,
            serial,
            memorymap,
            build_year,
            build_week,
            cache_dir,
            on_load_finished,
        )
        self.group_members: dict[int, set[int]] = {}

    def get_initial_timeout(self) -> int:
        """Get initial timeout for loading this module."""
        return 100000

    async def _load_default_channels(self) -> None:
        for chan in range(1, 64 + 1):
            self._channels[chan] = Channel(
                module=self,
                num=chan,
                name="placeholder",
                nameEditable=True,
                subDevice=True,
                writer=self._writer,
                address=self._address,
            )
            # Placeholders will keep this module loading
            # Until the DaliDeviceSettings messages either delete or replace these placeholder's
            # with actual channels
        await self._request_dali_channels()

    async def _request_dali_channels(self) -> None:
        msg_type = commandRegistry.get_command(
            DALI_DEVICE_SETTINGS_REQUEST_COMMAND_CODE, self.get_type()
        )
        if msg_type is None:
            return
        msg = instantiate_command(msg_type, self._address)
        msg.priority = PRIORITY_LOW
        setattr(msg, "channel", 81)  # all
        setattr(msg, "settings", None)  # all
        await self._writer(msg)

    async def on_message(self, message: Message) -> None:
        """Process received message."""
        if isinstance(message, DaliDeviceSettingMsg):
            if isinstance(message.data, DaliDeviceTypeMsg):
                if message.data.device_type == DaliDeviceType.NoDevicePresent:
                    if message.channel in self._channels:
                        del self._channels[message.channel]
                else:
                    # Any present DALI device (LedModule, Dimmer, and the other
                    # lamp types) is exposed as a dimmable channel. Only
                    # NoDevicePresent slots are removed above.
                    cache = self._loaded_cache
                    if (
                        "channels" in cache
                        and str(message.channel) in cache["channels"]
                        and cache["channels"][str(message.channel)]["type"] == "Dimmer"
                    ):
                        # If we have a cached dimmer channel, use that name
                        name = cache["channels"][str(message.channel)]["name"]
                        self._channels[message.channel] = Dimmer(
                            self,
                            message.channel,
                            name,
                            False,  # set False to enable an already loaded Dimmer
                            True,
                            self._writer,
                            self._address,
                            slider_scale=254,
                        )
                    elif self._channels.get(message.channel).__class__ != Dimmer:
                        # New or changed type, replace channel:
                        self._channels[message.channel] = Dimmer(
                            self,
                            message.channel,
                            "",
                            True,
                            True,
                            self._writer,
                            self._address,
                            slider_scale=254,
                        )
                        await self._request_single_channel_name(message.channel)

            elif isinstance(message.data, MemberOfGroupMsg):
                for group in range(15 + 1):
                    this_group_members = self.group_members.setdefault(group, set())
                    if message.data.member_of_group[group]:
                        this_group_members.add(message.channel)
                    elif message.channel in this_group_members:
                        this_group_members.remove(message.channel)

        elif isinstance(message, PushButtonStatusMessage):
            _channel_offset = self.calc_channel_offset(message.address)
            for channel in message.opened:
                if _channel_offset + channel > 64:  # ignore groups
                    continue
                await self._update_channel((_channel_offset + channel), {"state": 0})
            # ignore message.closed: we don't know at what dimlevel they're started

        elif isinstance(message, DimValueStatus):
            for offset, dim_value in enumerate(message.dim_values):
                channel = message.channel + offset
                if channel <= 64:  # channel
                    await self._update_channel(channel, {"state": dim_value})
                elif channel <= 80:  # group
                    group_num = channel - 65
                    for chan in self.group_members.get(group_num, []):
                        await self._update_channel(chan, {"state": dim_value})
                else:  # broadcast
                    for channel_obj in self._channels.values():
                        await channel_obj.update({"state": dim_value})

        elif isinstance(
            message,
            (
                SetLedMessage,
                ClearLedMessage,
                FastBlinkingLedMessage,
                SlowBlinkingLedMessage,
            ),
        ):
            pass

        else:
            return await super().on_message(message)
        return None

    async def _request_channel_name(self) -> None:
        # Channel names are requested after channel scan
        # don't do them here (at initialization time)
        pass

    async def _request_single_channel_name(self, channel_num: int) -> None:
        msg_type = commandRegistry.get_command(
            CHANNEL_NAME_REQUEST_COMMAND_CODE, self.get_type()
        )
        if msg_type is None:
            return
        msg = instantiate_command(msg_type, self._address)
        msg.priority = PRIORITY_LOW
        setattr(msg, "channels", channel_num)
        await self._writer(msg)


__all__ = ["Module", "VmbDali", "_coerce_cached_sub_address"]
