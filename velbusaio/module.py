"""This represents a velbus module."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import importlib.resources
import json
import logging
import pathlib
import struct
import sys
from typing import TYPE_CHECKING

from aiofile import async_open

if TYPE_CHECKING:
    from velbusaio.controller import Controller

from velbusaio import channels as channels_module, properties as properties_module
from velbusaio.channels import (
    Button,
    ButtonCounter,
    Channel,
    Dimmer,
    Temperature as TemperatureChannelType,
)
from velbusaio.command_registry import commandRegistry
from velbusaio.const import PRIORITY_LOW, SCAN_MODULEINFO_TIMEOUT_INITIAL
from velbusaio.helpers import h2, handle_match, keys_exists
from velbusaio.message import Message
from velbusaio.messages.blind_status import BlindStatusMessage, BlindStatusNgMessage
from velbusaio.messages.channel_name_part1 import (
    ChannelNamePart1Message,
    ChannelNamePart1Message2,
    ChannelNamePart1Message3,
)
from velbusaio.messages.channel_name_part2 import (
    ChannelNamePart2Message,
    ChannelNamePart2Message2,
    ChannelNamePart2Message3,
)
from velbusaio.messages.channel_name_part3 import (
    ChannelNamePart3Message,
    ChannelNamePart3Message2,
    ChannelNamePart3Message3,
)
from velbusaio.messages.channel_name_request import (
    COMMAND_CODE as CHANNEL_NAME_REQUEST_COMMAND_CODE,
    ChannelNameRequestMessage,
)
from velbusaio.messages.clear_led import ClearLedMessage
from velbusaio.messages.counter_status import CounterStatusMessage
from velbusaio.messages.counter_status_request import CounterStatusRequestMessage
from velbusaio.messages.counter_value import CounterValueMessage
from velbusaio.messages.dali_device_settings import (
    DaliDeviceSettingMsg,
    DeviceType as DaliDeviceType,
    DeviceTypeMsg as DaliDeviceTypeMsg,
    MemberOfGroupMsg,
)
from velbusaio.messages.dali_device_settings_request import (
    COMMAND_CODE as DALI_DEVICE_SETTINGS_REQUEST_COMMAND_CODE,
    DaliDeviceSettingsRequest,
)
from velbusaio.messages.dali_dim_value_status import DimValueStatus
from velbusaio.messages.dimmer_channel_status import DimmerChannelStatusMessage
from velbusaio.messages.dimmer_status import DimmerStatusMessage
from velbusaio.messages.fast_blinking_led import FastBlinkingLedMessage
from velbusaio.messages.memory_data import MemoryDataMessage
from velbusaio.messages.memory_data_block import MemoryDataBlockMessage
from velbusaio.messages.module_status import (
    ModuleStatusGP4PirMessage,
    ModuleStatusMessage,
    ModuleStatusMessage2,
    ModuleStatusPirMessage,
)
from velbusaio.messages.module_status_request import ModuleStatusRequestMessage
from velbusaio.messages.module_type_request import ModuleTypeRequestMessage
from velbusaio.messages.psu_load import PsuLoadMessage
from velbusaio.messages.psu_values import PsuValuesMessage
from velbusaio.messages.push_button_status import PushButtonStatusMessage
from velbusaio.messages.raw import MeteoRawMessage, SensorRawMessage
from velbusaio.messages.read_data_block_from_memory import (
    ReadDataBlockFromMemoryMessage,
)
from velbusaio.messages.read_data_from_memory import ReadDataFromMemoryMessage
from velbusaio.messages.relay_status import RelayStatusMessage, RelayStatusMessage2
from velbusaio.messages.sensor_temperature import SensorTemperatureMessage
from velbusaio.messages.set_led import SetLedMessage
from velbusaio.messages.slider_status import SliderStatusMessage
from velbusaio.messages.slow_blinking_led import SlowBlinkingLedMessage
from velbusaio.messages.temp_sensor_status import TempSensorStatusMessage
from velbusaio.messages.update_led_status import UpdateLedStatusMessage
from velbusaio.properties import Property


class Module:
    """Abstract class for Velbus hardware modules."""

    @classmethod
    def factory(
        cls,
        module_address: int,
        module_type: int,
        serial: int | None = None,
        memorymap: int | None = None,
        build_year: int | None = None,
        build_week: int | None = None,
        cache_dir: str | None = None,
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
            )

        return Module(
            module_address,
            module_type,
            serial,
            memorymap,
            build_year,
            build_week,
            cache_dir,
        )

    def __init__(
        self,
        module_address: int,
        module_type: int,
        serial: int | None = None,
        memorymap: int | None = None,
        build_year: int | None = None,
        build_week: int | None = None,
        cache_dir: str | None = None,
    ) -> None:
        """Initialize Module object."""
        self._address = module_address
        self._type = int(module_type)
        self._data = {}

        self._name = {}
        self._sub_address = {}
        self.serial = serial
        self.memory_map_version = memorymap
        self.build_year = build_year
        self.build_week = build_week
        self._cache_dir = cache_dir
        self._is_loading = False
        self._got_status = asyncio.Event()
        self._got_status.clear()
        self._channels: dict[int, Channel] = {}
        self._properties: dict[str, Property] = {}
        self.loaded = False
        self._use_cache = True
        self._loaded_cache = {}

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
        # load the protocol data
        try:
            if sys.version_info >= (3, 13):
                with importlib.resources.path(
                    __name__, f"module_spec/{h2(self._type)}.json"
                ) as fspath:
                    async with async_open(fspath) as protocol_file:
                        self._data = json.loads(await protocol_file.read())
            else:
                async with async_open(
                    str(
                        importlib.resources.files(__name__.split(".")[0]).joinpath(
                            f"module_spec/{h2(self._type)}.json"
                        )
                    )
                ) as protocol_file:
                    self._data = json.loads(await protocol_file.read())
            self._log.debug(f"Module spec {h2(self._type)} loaded")
        except FileNotFoundError:
            self._log.warning(f"No module spec for {h2(self._type)}")
            self._data = {}

        # set some params from the velbus controller
        self._writer = writer
        for chan in self._channels.values():
            chan.set_writer(writer)

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

    async def _cache(self) -> None:
        if not self._use_cache:
            return
        cfile = pathlib.Path(f"{self._cache_dir}/{self._address}.json")
        async with async_open(cfile, "w") as fl:
            await fl.write(json.dumps(self.to_cache(), indent=4))

    def __getstate__(self) -> dict:
        """Get state for pickling."""
        d = self.__dict__
        return {k: d[k] for k in d if k not in {"_writer", "_log", "_controller"}}

    def __setstate__(self, state: dict) -> None:
        """Set state for unpickling."""
        self.__dict__ = state

    def __repr__(self) -> str:
        """Return string representation of the module."""
        return f"<{self._name} type:{self._type} address:{self._address} loaded:{self.loaded} loading:{self._is_loading} channels: {self._channels} properties: {self._properties}>"

    def __str__(self) -> str:
        """Return string representation of the module."""
        return self.__repr__()

    def to_cache(self) -> dict:
        """Build cache dict."""
        d = {"name": self._name, "channels": {}, "sub_addresses": {}, "properties": {}}
        for num, chan in self._channels.items():
            d["channels"][num] = chan.to_cache()
        for num, address in self._sub_address.items():
            d["sub_addresses"][num] = address
        for num, prop in self._properties.items():
            d["properties"][num] = prop.to_cache()
        return d

    def get_address(self) -> int:
        """Get the module address."""
        return self._address

    def get_addresses(self) -> list:
        """Get all addresses for this module."""
        res = [self._address]
        res.extend(self._sub_address.values())
        return res

    def add_subaddress(self, num, addr) -> None:
        """Add a subaddress to this module."""
        self._sub_address[num] = addr

    def get_type(self) -> int:
        """Get the module type."""
        return self._type

    def get_type_name(self) -> str:
        """Get the module type name."""
        if "Type" in self._data:
            return self._data["Type"]
        return "UNKNOWN"

    def get_serial(self) -> str | None:
        """Get the module serial number."""
        return self.serial

    def get_name(self) -> str:
        """Get the module name."""
        return self._name

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

    async def on_message(self, message: Message) -> None:  # noqa: C901
        """Process received message."""
        self._log.debug(f"RX: {message}")
        _channel_offset = self.calc_channel_offset(message.address)

        if isinstance(
            message,
            (
                ChannelNamePart1Message,
                ChannelNamePart1Message2,
                ChannelNamePart1Message3,
            ),
        ):
            self._process_channel_name_message(1, message)
            await self._cache()
        elif isinstance(
            message,
            (
                ChannelNamePart2Message,
                ChannelNamePart2Message2,
                ChannelNamePart2Message3,
            ),
        ):
            self._process_channel_name_message(2, message)
            await self._cache()
        elif isinstance(
            message,
            (
                ChannelNamePart3Message,
                ChannelNamePart3Message2,
                ChannelNamePart3Message3,
            ),
        ):
            self._process_channel_name_message(3, message)
            await self._cache()
        elif isinstance(message, MemoryDataMessage):
            await self._process_memory_data_message(message)
        elif isinstance(message, MemoryDataBlockMessage):
            await self._process_memory_data_block_message(message)
        elif isinstance(message, (RelayStatusMessage, RelayStatusMessage2)):
            await self._update_channel(
                message.channel,
                {
                    "on": message.is_on(),
                    "inhibit": message.is_inhibited(),
                    "forced_on": message.is_forced_on(),
                    "disabled": message.is_disabled(),
                },
            )
        elif isinstance(message, SensorTemperatureMessage):
            chan = self._translate_channel_name(self._data["TemperatureChannel"])
            await self._channels[chan].maybe_update_temperature(
                message.getCurTemp(), 1 / 64
            )
            await self._update_channel(
                chan,
                {
                    "min": message.getMinTemp(),
                    "max": message.getMaxTemp(),
                },
            )
        elif isinstance(message, TempSensorStatusMessage):
            # update the current temp
            chan = self._translate_channel_name(self._data["TemperatureChannel"])
            if chan in self._channels:
                await self._update_channel(
                    chan,
                    {
                        "target": message.target_temp,
                        "cmode": message.mode_str,
                        "cstatus": message.status_str,
                        "sleep_timer": message.sleep_timer,
                        "cool_mode": message.cool_mode,
                    },
                )
                await self._channels[chan].maybe_update_temperature(
                    message.current_temp, 1 / 2
                )
            # update the thermostat channels
            channel_name_to_msg_prop_map = {
                "Heater": "heater",
                "Boost": "boost",
                "Pump": "pump",
                "Cooler": "cooler",
                "Alarm 1": "alarm1",
                "Alarm 2": "alarm2",
                "Alarm 3": "alarm3",
                "Alarm 4": "alarm4",
            }
            for channel_str in self._data["Channels"]:
                if keys_exists(self._data, "Channels", channel_str, "Type"):
                    if (
                        self._data["Channels"][channel_str]["Type"]
                        == "ThermostatChannel"
                    ):
                        channel = self._translate_channel_name(channel_str)
                        channel_name = self._data["Channels"][channel_str]["Name"]
                        if channel in self._channels:
                            await self._update_channel(
                                channel,
                                {
                                    "closed": getattr(
                                        message,
                                        channel_name_to_msg_prop_map[channel_name],
                                    )
                                },
                            )
        elif isinstance(message, PushButtonStatusMessage):
            _update_buttons = False
            for channel_types in self._data["Channels"]:
                if keys_exists(self._data, "Channels", channel_types, "Type"):
                    if (
                        self._data["Channels"][channel_types]["Type"] == "Button"
                        or self._data["Channels"][channel_types]["Type"] == "Sensor"
                        or self._data["Channels"][channel_types]["Type"]
                        == "ButtonCounter"
                    ):
                        _update_buttons = True
                        break
            if _update_buttons:
                for channel_id in range(1, 9):
                    channel = self._translate_channel_name(channel_id + _channel_offset)
                    if channel_id in message.closed:
                        await self._update_channel(channel, {"closed": True})
                    if channel_id in message.closed_long:
                        await self._update_channel(channel, {"long": True})
                    if channel_id in message.opened:
                        await self._update_channel(
                            channel, {"closed": False, "long": False}
                        )
        elif isinstance(message, (ModuleStatusMessage)):
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + _channel_offset)
                if channel_id in message.closed:
                    await self._update_channel(channel, {"closed": True})
                elif channel in self._channels and isinstance(
                    self._channels[channel], (Button, ButtonCounter)
                ):
                    await self._update_channel(channel, {"closed": False})
        elif isinstance(message, (ModuleStatusMessage2)):
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + _channel_offset)
                if channel_id in message.closed:
                    await self._update_channel(channel, {"closed": True})
                elif isinstance(self._channels[channel], (Button, ButtonCounter)):
                    await self._update_channel(channel, {"closed": False})
                if channel_id in message.enabled:
                    await self._update_channel(channel, {"enabled": True})
                elif channel in self._channels and isinstance(
                    self._channels[channel], (Button, ButtonCounter)
                ):
                    await self._update_channel(channel, {"enabled": False})
            # self.selected_program_str = message.selected_program_str
            await self._update_property(
                "selected_program",
                {"selected_program_str": message.selected_program_str},
            )
        elif isinstance(message, CounterStatusMessage) and isinstance(
            self._channels[message.channel], ButtonCounter
        ):
            channel = self._translate_channel_name(message.channel)
            await self._update_channel(
                channel,
                {
                    "pulses": message.pulses,
                    "counter": message.counter,
                    "delay": message.delay,
                },
            )
        elif isinstance(message, ModuleStatusPirMessage):
            await self._update_property("light_value", {"cur": message.light_value})
            await self._update_channel(1, {"closed": message.dark})
            await self._update_channel(2, {"closed": message.light})
            await self._update_channel(3, {"closed": message.motion1})
            await self._update_channel(4, {"closed": message.light_motion1})
            await self._update_channel(5, {"closed": message.motion2})
            await self._update_channel(6, {"closed": message.light_motion2})
            if 7 in self._channels:
                await self._update_channel(7, {"closed": message.low_temp_alarm})
            if 8 in self._channels:
                await self._update_channel(8, {"closed": message.high_temp_alarm})
            # self.selected_program_str = message.selected_program_str
            await self._update_property(
                "selected_program",
                {"selected_program_str": message.selected_program_str},
            )
        elif isinstance(message, ModuleStatusGP4PirMessage):
            await self._update_property("light_value", {"cur": message.light_value})
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + _channel_offset)
                await self._update_channel(
                    channel, {"closed": channel_id in message.closed}
                )
                if type(self._channels[channel]) is Button:
                    # only treat 'enabled' if the channel is a Button
                    await self._update_channel(
                        channel, {"enabled": channel_id in message.enabled}
                    )
            # self.selected_program_str = message.selected_program_str
            await self._update_property(
                "selected_program",
                {"selected_program_str": message.selected_program_str},
            )
        elif isinstance(message, UpdateLedStatusMessage):
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + _channel_offset)
                if channel_id in message.led_slow_blinking:
                    await self._update_channel(channel, {"led_state": "slow"})
                if channel_id in message.led_fast_blinking:
                    await self._update_channel(channel, {"led_state": "fast"})
                if channel_id in message.led_on:
                    await self._update_channel(channel, {"led_state": "on"})
                if (
                    channel_id not in message.led_slow_blinking
                    and channel_id not in message.led_fast_blinking
                    and channel_id not in message.led_on
                ):
                    await self._update_channel(channel, {"led_state": "off"})
        elif isinstance(message, SetLedMessage):
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + _channel_offset)
                if channel_id in message.leds:
                    await self._update_channel(channel, {"led_state": "on"})
        elif isinstance(message, ClearLedMessage):
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + _channel_offset)
                if channel_id in message.leds:
                    await self._update_channel(channel, {"led_state": "off"})
        elif isinstance(message, SlowBlinkingLedMessage):
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + _channel_offset)
                if channel_id in message.leds:
                    await self._update_channel(channel, {"led_state": "slow"})
        elif isinstance(message, FastBlinkingLedMessage):
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + _channel_offset)
                if channel_id in message.leds:
                    await self._update_channel(channel, {"led_state": "fast"})
        elif isinstance(message, (DimmerChannelStatusMessage, DimmerStatusMessage)):
            channel = self._translate_channel_name(message.channel)
            await self._update_channel(channel, {"state": message.cur_dimmer_state()})
        elif isinstance(message, SliderStatusMessage):
            channel = self._translate_channel_name(message.channel)
            await self._update_channel(channel, {"state": message.cur_slider_state()})
        elif isinstance(message, BlindStatusNgMessage):
            channel = self._translate_channel_name(message.channel)
            await self._update_channel(
                channel, {"state": message.status, "position": message.position}
            )
        elif isinstance(message, BlindStatusMessage):
            channel = self._translate_channel_name(message.channel)
            await self._update_channel(channel, {"state": message.status})
        elif isinstance(message, MeteoRawMessage):
            await self._update_channel(11, {"cur": message.rain})
            await self._update_channel(12, {"cur": message.light})
            await self._update_channel(13, {"cur": message.wind})
        elif isinstance(message, SensorRawMessage):
            await self._update_channel(
                message.sensor, {"cur": message.value, "unit": message.unit}
            )
        elif isinstance(message, CounterValueMessage):
            await self._update_channel(
                message.channel, {"power": message.power, "energy": message.energy}
            )
        elif isinstance(message, DimValueStatus):
            for offset, dim_value in enumerate(message.dim_values):
                channel = message.channel + offset
                await self._update_channel(channel, {"state": dim_value})
        elif isinstance(message, PsuLoadMessage):
            await self._update_property("psu_load_out", {"cur": message.out})
            await self._update_property("psu_load_1", {"cur": message.load_1})
            await self._update_property("psu_load_2", {"cur": message.load_2})
        elif isinstance(message, PsuValuesMessage):
            if message.channel == 3:
                suffix = "out"
            else:
                suffix = f"{message.channel}"
            await self._update_property(f"psu_power_{suffix}", {"cur": message.watt})
            await self._update_property(f"psu_voltage_{suffix}", {"cur": message.volt})
            await self._update_property(f"psu_current_{suffix}", {"cur": message.amp})
        # notify status
        self._got_status.set()

    async def _update_channel(self, channel: int, updates: dict):
        try:
            await self._channels[channel].update(updates)
        except KeyError:
            self._log.info(
                f"channel {channel} does not exist for module @ address {self}"
            )

    async def _update_property(self, property_name: str, updates: dict):
        try:
            await self._properties[property_name].update(updates)
        except KeyError:
            self._log.info(
                f"property {property_name} does not exist for module @ address {self}"
            )

    def get_channels(self) -> dict:
        """List all channels for this module."""
        return self._channels

    def get_properties(self) -> dict[str, Property]:
        """List all properties for this module."""
        return self._properties

    async def load_from_vlp(self, vlp_data: dict) -> None:
        """Initialize the module from VLP data."""
        self._is_loading = True
        self._use_cache = False
        self._name = vlp_data.get_name()
        self._data["Channels"] = vlp_data.get_channels()
        await self._load_default_channels()
        await self._load_properties()
        for chan in self._channels.values():
            chan.set_loaded(True)
        self.loaded = True
        self._is_loading = False
        await self._request_module_status()

    async def load(self, from_cache: bool = False) -> None:
        """Initialize the module."""
        # start the loading
        self._is_loading = True
        # see if we have a cache
        cache = await self._get_cache()
        self._loaded_cache = cache
        # load default channels
        await self._load_default_channels()
        await self._load_properties()

        # load the data from memory ( the stuff that we need)
        if "name" in cache and cache["name"] != "":
            self._name = cache["name"]
        else:
            await self.__load_memory()

        # load the sub addresses from cache if it's available
        if (self._use_cache or from_cache) and "sub_addresses" in cache:
            for num, addr in cache["sub_addresses"].items():
                self._sub_address[int(num)] = int(addr)
        else:
            # Submit ModuleType request to trigger discovery of sub addresses.
            # Do not cache immediately here: sub addresses are populated asynchronously
            # when the response is handled; caching now could store an empty mapping.
            await self._writer(ModuleTypeRequestMessage(self._address))

        # load the module status
        # await self._request_module_status()
        # load the channel names
        if "channels" in cache:
            for num, chan in cache["channels"].items():
                self._channels[int(num)].set_name(chan["name"])
                if "subdevice" in chan:
                    self._channels[int(num)].set_sub_device(chan["subdevice"])
                else:
                    self._channels[int(num)].set_sub_device(False)
                if "Unit" in chan:
                    self._channels[int(num)].set_unit(chan["Unit"])
                self._channels[int(num)].set_loaded(True)
        else:
            await self._request_channel_name()
        # load the module specific stuff
        self._load()
        # stop the loading
        self._is_loading = False
        await self._request_module_status()

    async def _get_cache(self):
        try:
            cfile = pathlib.Path(f"{self._cache_dir}/{self._address}.json")
            async with async_open(cfile, "r") as fl:
                cache = json.loads(await fl.read())
        except OSError:
            cache = {}
        return cache

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
        if "memo_text" not in self._properties:
            return
        await self._properties["memo_text"].set(txt)

    async def _process_memory_data_block_message(
        self, message: MemoryDataBlockMessage
    ) -> None:
        addr = f"{message.high_address:02X}{message.low_address:02X}"
        if "Memory" not in self._data:
            return
        # TODO this can also be SensorName, implement that also
        if "ModuleName" not in self._data["Memory"]:
            return
        addr_data = self._data["Memory"]["ModuleName"]
        if not isinstance(self._name, dict):
            # Already loaded as string, skip
            return
        # Parse address ranges: "00DD-00E9;01DD-01E9;02DD-02E9;03DD-03E9;04DD-04E8"
        ranges = []
        byte_offset = 0
        for block in addr_data.split(";"):
            start_str, end_str = block.split("-")
            start_addr = int("0x" + start_str, 0)
            end_addr = int("0x" + end_str, 0)
            ranges.append((start_addr, end_addr, byte_offset))
            byte_offset += end_addr - start_addr + 1
        # Check if incoming address falls within any range
        incoming_addr = int("0x" + addr, 0)
        for start_addr, end_addr, range_byte_offset in ranges:
            if start_addr <= incoming_addr <= end_addr:
                # Calculate the position within the overall module name
                position_in_range = incoming_addr - start_addr
                base_position = range_byte_offset + position_in_range
                # Store each byte from the message data
                for i, byte_val in enumerate(message.data):
                    char_position = base_position + i
                    self._name[char_position] = chr(byte_val)
                # Check if we've received all bytes (check if all positions are filled)
                total_bytes = ranges[-1][2] + (ranges[-1][1] - ranges[-1][0] + 1)
                if len(self._name) >= total_bytes:
                    # Convert to string, excluding 0xFF bytes
                    self._name = "".join(
                        str(x) for x in self._name.values() if x != chr(0xFF)
                    )
                    await self._cache()
                break

    async def _process_memory_data_message(self, message: MemoryDataMessage) -> None:
        addr = f"{message.high_address:02X}{message.low_address:02X}"
        if "Memory" not in self._data:
            return
        if "Address" not in self._data["Memory"]:
            return
        mdata = self._data["Memory"]["Address"][addr]
        if "Match" in mdata:
            for chan, chan_data in handle_match(mdata["Match"], message.data).items():
                data = chan_data.copy()
                await self._update_channel(chan, data)
        else:
            self._log.debug(mdata)

    def _process_channel_name_message(self, part: int, message: Message) -> None:
        channel = self._translate_channel_name(message.channel)
        if channel not in self._channels:
            return
        self._channels[channel].set_name_part(part, message.name)

    def _translate_channel_name(self, channel: str) -> int:
        if keys_exists(
            self._data,
            "ChannelNumbers",
            "Name",
            "Map",
            f"{int(channel):02X}",
        ):
            return int(
                self._data["ChannelNumbers"]["Name"]["Map"][f"{int(channel):02X}"]
            )
        return int(channel)

    async def is_loaded(self) -> bool:
        """Check if all name messages have been received."""
        # if we are loaded, just return
        if self.loaded:
            return True
        if self._is_loading:
            return False
        # the name should be loaded
        if isinstance(self._name, dict):
            return False
        # all channel names should be loaded
        for chan in self._channels.values():
            if not chan.is_loaded():
                return False
        # set that  we finished the module loading
        self.loaded = True
        await self._cache()
        return True

    async def _request_module_status(self) -> None:
        """Request current state of channels."""
        if "Channels" not in self._data:
            # some modules have no channels
            return
        self._log.info(f"Request module status {self._address}")

        mod_stat_req_msg = ModuleStatusRequestMessage(self._address)
        counter_msg = None
        if keys_exists(self._data, "AllChannelStatus"):
            mod_stat_req_msg.channels = self._data["AllChannelStatus"]
        else:
            for chan, chan_data in self._data["Channels"].items():
                if int(chan) < 9 and chan_data["Type"] in ("Blind", "Dimmer", "Relay"):
                    mod_stat_req_msg.channels.append(int(chan))
                if chan_data["Type"] == "ButtonCounter":
                    if counter_msg is None:
                        counter_msg = CounterStatusRequestMessage(self._address)
                    counter_msg.channels.append(int(chan))
        await self._writer(mod_stat_req_msg)
        if counter_msg is not None:
            await self._writer(counter_msg)

    async def _request_channel_name(self) -> None:
        # request the module channel names
        if keys_exists(self._data, "AllChannelStatus"):
            msg = ChannelNameRequestMessage(self._address)
            msg.priority = PRIORITY_LOW
            msg.channels = 0xFF
            await self._writer(msg)
        else:
            msg_type = commandRegistry.get_command(
                CHANNEL_NAME_REQUEST_COMMAND_CODE, self.get_type()
            )
            msg = msg_type(self._address)
            msg.priority = PRIORITY_LOW
            msg.channels = list(range(1, (self.number_of_channels() + 1)))
            await self._writer(msg)

    async def __load_memory(self) -> None:
        """Request all needed memory addresses."""
        if "Memory" not in self._data:
            self._name = None
            return

        if self._type == 0x0C:
            self._name = None
            return

        for memory_key, memory_part in self._data["Memory"].items():
            if memory_key == "Address":
                for addr_int in memory_part:
                    addr = struct.unpack(
                        ">BB", struct.pack(">h", int("0x" + addr_int, 0))
                    )
                    msg = ReadDataFromMemoryMessage(self._address)
                    msg.priority = PRIORITY_LOW
                    msg.high_address = addr[0]
                    msg.low_address = addr[1]
                    await self._writer(msg)
            elif memory_key in {"ModuleName", "SensorName"}:
                # example:
                # "ModuleName": "00DD-00E9;01DD-01E9;02DD-02E9;03DD-03E9;04DD-04E8",
                # request using MermoryDataBlock message, requests 4 bytes
                for block in memory_part.split(";"):
                    addr_start_str, addr_end_str = block.split("-")
                    # Convert to integer addresses
                    addr_start_int = int("0x" + addr_start_str, 0)
                    addr_end_int = int("0x" + addr_end_str, 0)
                    # Split into 4-byte blocks
                    current_addr = addr_start_int
                    while current_addr <= addr_end_int:
                        block_end = min(
                            current_addr + 3, addr_end_int
                        )  # 4 bytes = current + 3
                        # Convert back to high/low address bytes
                        addr_start = struct.unpack(
                            ">BB", struct.pack(">h", current_addr)
                        )
                        msg = ReadDataBlockFromMemoryMessage(self._address)
                        msg.priority = PRIORITY_LOW
                        msg.high_address = addr_start[0]
                        msg.low_address = addr_start[1]
                        await self._writer(msg)
                        current_addr = block_end + 1

    async def _load_properties(self) -> None:
        """Method for per module type loading of properties."""
        if "Properties" not in self._data:
            return

        for prop, prop_data in self._data["Properties"].items():
            if "Type" not in prop_data:
                continue
            prop_type = prop_data["Type"]
            try:
                cls = getattr(properties_module, prop_type)
            except AttributeError:
                self._log.error(
                    "Unknown property type '%s' for property '%s' on module address %s",
                    prop_type,
                    prop,
                    getattr(self, "_address", "unknown"),
                )
                continue
            self._properties[prop] = cls(
                module=self,
                name=prop,
                writer=self._writer,
            )

    async def _load_default_channels(self) -> None:
        if "Channels" not in self._data:
            return

        for chan, chan_data in self._data["Channels"].items():
            edit = True
            sub = True
            if "Editable" not in chan_data or chan_data["Editable"] != "yes":
                edit = False
            if "Subdevice" not in chan_data or chan_data["Subdevice"] != "yes":
                sub = False
            chan_type = chan_data["Type"]
            try:
                cls = getattr(channels_module, chan_type)
            except AttributeError:
                self._log.error(
                    "Unknown channel type '%s' for channel '%s' on module address %s",
                    chan_type,
                    chan,
                    getattr(self, "_address", "unknown"),
                )
                continue

            self._channels[int(chan)] = cls(
                module=self,
                num=int(chan),
                name=chan_data["Name"],
                nameEditable=edit,
                subDevice=sub,
                writer=self._writer,
                address=self._address,
            )
            if chan_data["Type"] == "Temperature":
                if "Thermostat" in self._data or (
                    "ThermostatAddr" in self._data and self._data["ThermostatAddr"] != 0
                ):
                    await self._update_channel(int(chan), {"thermostat": True})
            if chan_data["Type"] == "Dimmer" and "sliderScale" in self._data:
                self._channels[int(chan)].slider_scale = self._data["sliderScale"]


class VmbDali(Module):
    """DALI has a variable number of channels.

    Therefore we create a module that first creates 64 placeholder channels.
    After that it requests the DALI device settings to determine the actual channels.
    """

    def __init__(
        self,
        module_address: int,
        module_type: int,
        serial: int | None = None,
        memorymap: int | None = None,
        build_year: int | None = None,
        build_week: int | None = None,
        cache_dir: str | None = None,
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

    async def _request_dali_channels(self):
        msg_type = commandRegistry.get_command(
            DALI_DEVICE_SETTINGS_REQUEST_COMMAND_CODE, self.get_type()
        )
        msg: DaliDeviceSettingsRequest = msg_type(self._address)
        msg.priority = PRIORITY_LOW
        msg.channel = 81  # all
        msg.settings = None  # all
        await self._writer(msg)

    async def on_message(self, message: Message) -> None:
        """Process received message."""
        if isinstance(message, DaliDeviceSettingMsg):
            if isinstance(message.data, DaliDeviceTypeMsg):
                if message.data.device_type == DaliDeviceType.NoDevicePresent:
                    if message.channel in self._channels:
                        del self._channels[message.channel]
                elif message.data.device_type == DaliDeviceType.LedModule:
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
                            None,
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
                    for chan in self._channels.values():
                        await chan.update({"state": dim_value})

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
        msg = msg_type(self._address)
        msg.priority = PRIORITY_LOW
        msg.channels = channel_num
        await self._writer(msg)
