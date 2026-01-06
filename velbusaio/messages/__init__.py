"""Initialize Velbus message package.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.messages.blind_status import BlindStatusMessage, BlindStatusNgMessage
from velbusaio.messages.bus_active import BusActiveMessage
from velbusaio.messages.bus_error_counter_status import BusErrorCounterStatusMessage
from velbusaio.messages.bus_error_counter_status_request import (
    BusErrorStatusRequestMessage,
)
from velbusaio.messages.bus_off import BusOffMessage
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
    ChannelNameRequestMessage,
    ChannelNameRequestMessage2,
)
from velbusaio.messages.clear_led import ClearLedMessage
from velbusaio.messages.counter_status import CounterStatusMessage
from velbusaio.messages.counter_status_request import CounterStatusRequestMessage
from velbusaio.messages.counter_value import CounterValueMessage
from velbusaio.messages.cover_down import CoverDownMessage, CoverDownMessage2
from velbusaio.messages.cover_off import CoverOffMessage, CoverOffMessage2
from velbusaio.messages.cover_position import CoverPosMessage
from velbusaio.messages.cover_up import CoverUpMessage, CoverUpMessage2
from velbusaio.messages.dali_device_settings import DaliDeviceSettingMsg
from velbusaio.messages.dimmer_channel_status import DimmerChannelStatusMessage
from velbusaio.messages.dimmer_status import DimmerStatusMessage
from velbusaio.messages.fast_blinking_led import FastBlinkingLedMessage
from velbusaio.messages.forced_off import ForcedOff
from velbusaio.messages.forced_on import ForcedOn
from velbusaio.messages.interface_status_request import InterfaceStatusRequestMessage
from velbusaio.messages.ir_receiver_status import IRReceiverStatusMessage
from velbusaio.messages.kwh_status import KwhStatusMessage
from velbusaio.messages.light_value_request import LightValueRequest
from velbusaio.messages.memo_text import MemoTextMessage
from velbusaio.messages.memory_data import MemoryDataMessage
from velbusaio.messages.memory_data_block import MemoryDataBlockMessage
from velbusaio.messages.memory_dump_request import MemoryDumpRequestMessage
from velbusaio.messages.module_status import ModuleStatusMessage, ModuleStatusMessage2
from velbusaio.messages.module_status_request import ModuleStatusRequestMessage
from velbusaio.messages.module_subtype import ModuleSubTypeMessage
from velbusaio.messages.module_type import ModuleType2Message, ModuleTypeMessage
from velbusaio.messages.module_type_request import ModuleTypeRequestMessage
from velbusaio.messages.psu_load import PsuLoadMessage
from velbusaio.messages.psu_values import PsuValuesMessage
from velbusaio.messages.push_button_status import PushButtonStatusMessage
from velbusaio.messages.raw import MeteoRawMessage, SensorRawMessage
from velbusaio.messages.read_data_block_from_memory import (
    ReadDataBlockFromMemoryMessage,
)
from velbusaio.messages.read_data_from_memory import ReadDataFromMemoryMessage
from velbusaio.messages.realtime_clock_status_request import RealtimeClockStatusRequest
from velbusaio.messages.receive_buffer_full import ReceiveBufferFullMessage
from velbusaio.messages.receive_ready import ReceiveReadyMessage
from velbusaio.messages.relay_status import RelayStatusMessage
from velbusaio.messages.restore_dimmer import RestoreDimmerMessage
from velbusaio.messages.select_program import SelectProgramMessage
from velbusaio.messages.sensor_temp_request import SensorTempRequest
from velbusaio.messages.sensor_temperature import SensorTemperatureMessage
from velbusaio.messages.set_date import SetDate
from velbusaio.messages.set_daylight_saving import SetDaylightSaving
from velbusaio.messages.set_dimmer import SetDimmerMessage
from velbusaio.messages.set_led import SetLedMessage
from velbusaio.messages.set_realtime_clock import SetRealtimeClock
from velbusaio.messages.set_temperature import SetTemperatureMessage
from velbusaio.messages.slider_status import SliderStatusMessage
from velbusaio.messages.slow_blinking_led import SlowBlinkingLedMessage
from velbusaio.messages.start_relay_blinking_timer import StartRelayBlinkingTimerMessage
from velbusaio.messages.start_relay_timer import StartRelayTimerMessage
from velbusaio.messages.switch_relay_off import SwitchRelayOffMessage
from velbusaio.messages.switch_relay_on import SwitchRelayOnMessage
from velbusaio.messages.switch_to_comfort import SwitchToComfortMessage
from velbusaio.messages.switch_to_day import SwitchToDayMessage
from velbusaio.messages.switch_to_night import SwitchToNightMessage
from velbusaio.messages.switch_to_safe import SwitchToSafeMessage
from velbusaio.messages.temp_sensor_settings_part1 import TempSensorSettingsPart1
from velbusaio.messages.temp_sensor_settings_part2 import TempSensorSettingsPart2
from velbusaio.messages.temp_sensor_settings_part3 import TempSensorSettingsPart3
from velbusaio.messages.temp_sensor_settings_part4 import TempSensorSettingsPart4
from velbusaio.messages.temp_sensor_settings_request import TempSensorSettingsRequest
from velbusaio.messages.temp_sensor_status import TempSensorStatusMessage
from velbusaio.messages.temp_set_cooling import TempSetCoolingMessage
from velbusaio.messages.temp_set_heating import TempSetHeatingMessage
from velbusaio.messages.update_led_status import UpdateLedStatusMessage
from velbusaio.messages.very_fast_blinking_led import VeryFastBlinkingLedMessage
from velbusaio.messages.write_data_to_memory import WriteDataToMemoryMessage
from velbusaio.messages.write_memory_block import WriteMemoryBlockMessage
from velbusaio.messages.write_module_address_and_serial_number import (
    WriteModuleAddressAndSerialNumberMessage,
)

__all__ = [
    "BlindStatusMessage",
    "BlindStatusNgMessage",
    "BusActiveMessage",
    "BusErrorCounterStatusMessage",
    "BusErrorStatusRequestMessage",
    "BusOffMessage",
    "ChannelNamePart1Message",
    "ChannelNamePart1Message2",
    "ChannelNamePart1Message3",
    "ChannelNamePart2Message",
    "ChannelNamePart2Message2",
    "ChannelNamePart2Message3",
    "ChannelNamePart3Message",
    "ChannelNamePart3Message2",
    "ChannelNamePart3Message3",
    "ChannelNameRequestMessage",
    "ChannelNameRequestMessage2",
    "ClearLedMessage",
    "CounterStatusMessage",
    "CounterStatusRequestMessage",
    "CounterValueMessage",
    "CoverDownMessage",
    "CoverDownMessage2",
    "CoverOffMessage",
    "CoverOffMessage2",
    "CoverPosMessage",
    "CoverUpMessage",
    "CoverUpMessage2",
    "DaliDeviceSettingMsg",
    "DimmerChannelStatusMessage",
    "DimmerStatusMessage",
    "FastBlinkingLedMessage",
    "ForcedOff",
    "ForcedOn",
    "IRReceiverStatusMessage",
    "InterfaceStatusRequestMessage",
    "KwhStatusMessage",
    "LightValueRequest",
    "MemoTextMessage",
    "MemoryDataBlockMessage",
    "MemoryDataMessage",
    "MemoryDumpRequestMessage",
    "MeteoRawMessage",
    "ModuleStatusMessage",
    "ModuleStatusMessage2",
    "ModuleStatusRequestMessage",
    "ModuleSubTypeMessage",
    "ModuleType2Message",
    "ModuleTypeMessage",
    "ModuleTypeRequestMessage",
    "PsuLoadMessage",
    "PsuValuesMessage",
    "PushButtonStatusMessage",
    "ReadDataBlockFromMemoryMessage",
    "ReadDataFromMemoryMessage",
    "RealtimeClockStatusRequest",
    "ReceiveBufferFullMessage",
    "ReceiveReadyMessage",
    "RelayStatusMessage",
    "RestoreDimmerMessage",
    "SelectProgramMessage",
    "SensorRawMessage",
    "SensorTempRequest",
    "SensorTemperatureMessage",
    "SetDate",
    "SetDaylightSaving",
    "SetDimmerMessage",
    "SetLedMessage",
    "SetRealtimeClock",
    "SetTemperatureMessage",
    "SliderStatusMessage",
    "SlowBlinkingLedMessage",
    "StartRelayBlinkingTimerMessage",
    "StartRelayTimerMessage",
    "SwitchRelayOffMessage",
    "SwitchRelayOnMessage",
    "SwitchToComfortMessage",
    "SwitchToDayMessage",
    "SwitchToNightMessage",
    "SwitchToSafeMessage",
    "TempSensorSettingsPart1",
    "TempSensorSettingsPart2",
    "TempSensorSettingsPart3",
    "TempSensorSettingsPart4",
    "TempSensorSettingsRequest",
    "TempSensorStatusMessage",
    "TempSetCoolingMessage",
    "TempSetHeatingMessage",
    "UpdateLedStatusMessage",
    "VeryFastBlinkingLedMessage",
    "WriteDataToMemoryMessage",
    "WriteMemoryBlockMessage",
    "WriteModuleAddressAndSerialNumberMessage",
]
