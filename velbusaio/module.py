"""
This represents a velbus module
"""

from __future__ import annotations

import importlib.resources
import json
import logging
import os
import pathlib
import struct
import sys
from typing import Awaitable, Callable

from aiofile import async_open

from velbusaio.channels import (
    Blind,
    Button,
    ButtonCounter,
    Channel,
    Dimmer,
    EdgeLit,
    LightSensor,
    Memo,
    Relay,
    SelectedProgram,
    Sensor,
    SensorNumber,
)
from velbusaio.channels import Temperature
from velbusaio.channels import Temperature as TemperatureChannelType
from velbusaio.channels import (
    ThermostatChannel,
)
from velbusaio.command_registry import commandRegistry
from velbusaio.const import (
    CHANNEL_LIGHT_VALUE,
    CHANNEL_MEMO_TEXT,
    CHANNEL_SELECTED_PROGRAM,
    PRIORITY_LOW,
    SCAN_MODULEINFO_TIMEOUT_INITIAL,
)
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
)
from velbusaio.messages.channel_name_request import (
    ChannelNameRequestMessage,
)
from velbusaio.messages.clear_led import ClearLedMessage
from velbusaio.messages.counter_status import CounterStatusMessage
from velbusaio.messages.counter_status_request import CounterStatusRequestMessage
from velbusaio.messages.dali_device_settings import DaliDeviceSettingMsg
from velbusaio.messages.dali_device_settings import DeviceType as DaliDeviceType
from velbusaio.messages.dali_device_settings import DeviceTypeMsg as DaliDeviceTypeMsg
from velbusaio.messages.dali_device_settings import MemberOfGroupMsg
from velbusaio.messages.dali_device_settings_request import (
    COMMAND_CODE as DALI_DEVICE_SETTINGS_REQUEST_COMMAND_CODE,
)
from velbusaio.messages.dali_device_settings_request import (
    DaliDeviceSettingsRequest,
)
from velbusaio.messages.dali_dim_value_status import DimValueStatus
from velbusaio.messages.dimmer_channel_status import DimmerChannelStatusMessage
from velbusaio.messages.dimmer_status import DimmerStatusMessage
from velbusaio.messages.fast_blinking_led import FastBlinkingLedMessage
from velbusaio.messages.memory_data import MemoryDataMessage
from velbusaio.messages.module_status import (
    ModuleStatusGP4PirMessage,
    ModuleStatusMessage,
    ModuleStatusMessage2,
    ModuleStatusPirMessage,
)
from velbusaio.messages.module_status_request import ModuleStatusRequestMessage
from velbusaio.messages.push_button_status import PushButtonStatusMessage
from velbusaio.messages.raw import MeteoRawMessage, SensorRawMessage
from velbusaio.messages.read_data_from_memory import ReadDataFromMemoryMessage
from velbusaio.messages.relay_status import RelayStatusMessage, RelayStatusMessage2
from velbusaio.messages.sensor_temperature import SensorTemperatureMessage
from velbusaio.messages.set_led import SetLedMessage
from velbusaio.messages.slider_status import SliderStatusMessage
from velbusaio.messages.slow_blinking_led import SlowBlinkingLedMessage
from velbusaio.messages.temp_sensor_status import TempSensorStatusMessage
from velbusaio.messages.update_led_status import UpdateLedStatusMessage


class Module:
    """
    Abstract class for Velbus hardware modules.
    """

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
        if module_type == 0x45 or module_type == 0x5A:
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
        self._channels = {}
        self.loaded = False

    def get_initial_timeout(self) -> int:
        return SCAN_MODULEINFO_TIMEOUT_INITIAL

    async def initialize(self, writer: Callable[[Message], Awaitable[None]]) -> None:
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
            chan._writer = writer

    def cleanupSubChannels(self) -> None:
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
        cfile = pathlib.Path(f"{self._cache_dir}/{self._address}.json")
        async with async_open(cfile, "w") as fl:
            await fl.write(json.dumps(self.to_cache(), indent=4))

    def __getstate__(self) -> dict:
        d = self.__dict__
        self_dict = {k: d[k] for k in d if k != "_writer" and k != "_log"}
        return self_dict

    def __setstate__(self, state: dict) -> None:
        self.__dict__ = state

    def __repr__(self) -> str:
        return f"<{self._name} type:{self._type} address:{self._address} loaded:{self.loaded} loading:{self._is_loading} channels: {self._channels}>"

    def __str__(self) -> str:
        return self.__repr__()

    def to_cache(self) -> dict:
        d = {"name": self._name, "channels": {}}
        for num, chan in self._channels.items():
            d["channels"][num] = chan.to_cache()
        return d

    def get_addresses(self) -> list:
        """
        Get all addresses for this module
        """
        res = []
        res.append(self._address)
        for addr in self._sub_address.values():
            res.append(addr)
        return res

    def get_type(self) -> int:
        """
        Get the module type
        """
        return self._type

    def get_type_name(self) -> str:
        if "Type" in self._data:
            return self._data["Type"]
        return "UNKNOWN"

    def get_serial(self) -> str | None:
        return self.serial

    def get_name(self) -> str:
        return self._name

    def get_sw_version(self) -> str:
        return f"{self.serial}-{self.memory_map_version}.{self.build_year}.{self.build_week}"

    def calc_channel_offset(self, address: int) -> int:
        _channel_offset = 0
        if self._address != address:
            for _sub_addr_key, _sub_addr_val in self._sub_address.items():
                if _sub_addr_val == address:
                    _channel_offset = 8 * _sub_addr_key
                    break
        return _channel_offset

    async def on_message(self, message: Message) -> None:
        """
        Process received message
        """
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
            await self._update_channel(
                CHANNEL_SELECTED_PROGRAM,
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
            await self._update_channel(
                CHANNEL_LIGHT_VALUE, {"cur": message.light_value}
            )
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
            await self._update_channel(
                CHANNEL_SELECTED_PROGRAM,
                {"selected_program_str": message.selected_program_str},
            )
        elif isinstance(message, ModuleStatusGP4PirMessage):
            await self._update_channel(
                CHANNEL_LIGHT_VALUE, {"cur": message.light_value}
            )
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
            await self._update_channel(
                CHANNEL_SELECTED_PROGRAM,
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

    async def _update_channel(self, channel: int, updates: dict):
        try:
            await self._channels[channel].update(updates)
        except KeyError:
            self._log.info(
                f"channel {channel} does not exist for module @ address {self}"
            )

    def get_channels(self) -> dict:
        """
        List all channels for this module
        """
        return self._channels

    async def load(self, from_cache: bool = False) -> None:
        # start the loading
        self._is_loading = True
        # see if we have a cache
        try:
            cfile = pathlib.Path(f"{self._cache_dir}/{self._address}.json")
            async with async_open(cfile, "r") as fl:
                cache = json.loads(await fl.read())
        except OSError:
            cache = {}
        # load default channels
        await self._load_default_channels()

        # load the data from memory ( the stuff that we need)
        if "name" in cache and cache["name"] != "":
            self._name = cache["name"]
        else:
            await self.__load_memory()
        # load the module status
        # await self._request_module_status()
        # load the channel names
        if "channels" in cache:
            for num, chan in cache["channels"].items():
                self._channels[int(num)]._name = chan["name"]
                if "sub_device" in chan:
                    self._channels[int(num)]._sub_device = chan["sub_device"]
                else:
                    self._channels[int(num)]._sub_device = False
                if "Unit" in chan:
                    self._channels[int(num)]._Unit = chan["Unit"]
                self._channels[int(num)]._is_loaded = True
        else:
            await self._request_channel_name()
        # load the module specific stuff
        self._load()
        # stop the loading
        self._is_loading = False
        await self._request_module_status()

    def _load(self) -> None:
        """
        Method for per module type loading
        """
        pass

    def number_of_channels(self) -> int:
        """
        Retrieve the number of available channels in this module

        :return: int
        """
        if not len(self._channels):
            return 0
        return max(self._channels.keys())

    async def set_memo_text(self, txt: str) -> None:
        if CHANNEL_MEMO_TEXT not in self._channels.keys():
            return
        await self._channels[CHANNEL_MEMO_TEXT].set(txt)

    async def _process_memory_data_message(self, message: MemoryDataMessage) -> None:
        addr = "{high:02X}{low:02X}".format(
            high=message.high_address, low=message.low_address
        )
        if "Memory" not in self._data:
            return
        if "Address" not in self._data["Memory"]:
            return
        mdata = self._data["Memory"]["Address"][addr]
        if "ModuleName" in mdata and isinstance(self._name, dict):
            # if self._name is a dict we are still loading
            # if its a string it was already complete
            char_and_save = mdata["ModuleName"].split(":")
            char = char_and_save[0]
            self._name[int(char)] = chr(message.data)
            if len(char_and_save) > 1 and char_and_save[1] == "Save":
                self._name = "".join(
                    str(x) for x in self._name.values() if x != chr(0xFF)
                )
        elif "Match" in mdata:
            for chan, chan_data in handle_match(mdata["Match"], message.data).items():
                data = chan_data.copy()
                await self._update_channel(chan, data)
        elif "SensorName" in mdata:
            # this is part of the channel names
            # make sure we set the channel to loaded
            # format of the value (in mdata)
            #   channel:char:start/save
            spl = mdata["SensorName"].split(":")
            if len(spl) == 2:
                [chan, pos] = spl
            elif len(spl) == 3:
                [chan, pos, dummy] = spl
            chan = self._translate_channel_name(chan)
            self._channels[chan].set_name_char(pos, message.data)
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
        """
        Check if all name messages have been received
        """
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
        """
        Request all needed memory addresses
        """
        if "Memory" not in self._data:
            self._name = None
            return

        if self._type == 0x0C:
            self._name = None
            return

        for memory_key, memory_part in self._data["Memory"].items():

            if memory_key == "Address":
                for addr_int in memory_part.keys():
                    addr = struct.unpack(
                        ">BB", struct.pack(">h", int("0x" + addr_int, 0))
                    )
                    msg = ReadDataFromMemoryMessage(self._address)
                    msg.priority = PRIORITY_LOW
                    msg.high_address = addr[0]
                    msg.low_address = addr[1]
                    await self._writer(msg)

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
            cls = getattr(sys.modules[__name__], chan_data["Type"])
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


class VmbDali(Module):
    """
    DALI has a variable number of channels: the number of channels
    depends on the number of DALI devices on the DALI bus
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
        if isinstance(message, DaliDeviceSettingMsg):
            if isinstance(message.data, DaliDeviceTypeMsg):
                if message.data.device_type == DaliDeviceType.NoDevicePresent:
                    if message.channel in self._channels:
                        del self._channels[message.channel]
                elif message.data.device_type == DaliDeviceType.LedModule:
                    if self._channels.get(message.channel).__class__ != Dimmer:
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
                for group in range(0, 15 + 1):
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

        await self._cache()

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
