"""Inbound message dispatch and handlers for Velbus modules."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import inspect
from typing import Any

from velbusaio.channels import (
    Button,
    ButtonCounter,
    Sensor,
    Temperature as TemperatureChannelType,
)
from velbusaio.helpers import handle_match, keys_exists
from velbusaio.memory import join_address
from velbusaio.message import Message
from velbusaio.messages.blind_status import (
    BlindStatusMessage,
    BlindStatusNg20Message,
    BlindStatusNgMessage,
)
from velbusaio.messages.bus_error_counter_status import BusErrorCounterStatusMessage
from velbusaio.messages.cancel_forced_off import CancelForcedOff
from velbusaio.messages.cancel_forced_on import CancelForcedOn
from velbusaio.messages.cancel_inhibit import CancelInhibit
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
from velbusaio.messages.clear_led import ClearLedMessage
from velbusaio.messages.counter_status import CounterStatusMessage
from velbusaio.messages.counter_value import CounterValueMessage
from velbusaio.messages.cover_position import CoverPosMessage
from velbusaio.messages.dali_dim_value_status import DimValueStatus
from velbusaio.messages.dimmer_channel_status import DimmerChannelStatusMessage
from velbusaio.messages.dimmer_status import DimmerStatusMessage
from velbusaio.messages.fast_blinking_led import FastBlinkingLedMessage
from velbusaio.messages.forced_off import ForcedOff
from velbusaio.messages.forced_on import ForcedOn
from velbusaio.messages.inhibit import Inhibit
from velbusaio.messages.memory_data import MemoryDataMessage
from velbusaio.messages.memory_data_block import MemoryDataBlockMessage
from velbusaio.messages.module_status import (
    ModuleStatusGP4PirMessage,
    ModuleStatusMessage,
    ModuleStatusMessage2,
    ModuleStatusPirMessage,
)
from velbusaio.messages.psu_load import PsuLoadMessage
from velbusaio.messages.psu_values import PsuValuesMessage
from velbusaio.messages.push_button_status import PushButtonStatusMessage
from velbusaio.messages.raw import MeteoRawMessage, SensorRawMessage
from velbusaio.messages.relay_status import (
    RelayStatusMessage,
    RelayStatusMessage2,
    RelayStatusMessage3,
)
from velbusaio.messages.sensor_temperature import SensorTemperatureMessage
from velbusaio.messages.set_led import SetLedMessage
from velbusaio.messages.slider_status import SliderStatusMessage
from velbusaio.messages.slow_blinking_led import SlowBlinkingLedMessage
from velbusaio.messages.temp_sensor_settings_part1 import TempSensorSettingsPart1
from velbusaio.messages.temp_sensor_settings_part2 import TempSensorSettingsPart2
from velbusaio.messages.temp_sensor_settings_part3 import TempSensorSettingsPart3
from velbusaio.messages.temp_sensor_settings_part4 import TempSensorSettingsPart4
from velbusaio.messages.temp_sensor_status import TempSensorStatusMessage
from velbusaio.messages.update_led_status import UpdateLedStatusMessage
from velbusaio.module_state import ModuleMixinState


class ModuleMessageHandlersMixin(ModuleMixinState):
    """Mixin: wire-format command handlers and dispatch for :class:`~velbusaio.module.Module`."""

    def _build_message_handlers(
        self,
    ) -> dict[type[Message], Callable[..., Awaitable[None]]]:
        """Build dispatch table for message handlers."""
        return {
            # Channel name messages
            ChannelNamePart1Message: self._handle_channel_name_part1,
            ChannelNamePart1Message2: self._handle_channel_name_part1,
            ChannelNamePart1Message3: self._handle_channel_name_part1,
            ChannelNamePart2Message: self._handle_channel_name_part2,
            ChannelNamePart2Message2: self._handle_channel_name_part2,
            ChannelNamePart2Message3: self._handle_channel_name_part2,
            ChannelNamePart3Message: self._handle_channel_name_part3,
            ChannelNamePart3Message2: self._handle_channel_name_part3,
            ChannelNamePart3Message3: self._handle_channel_name_part3,
            # Memory messages
            MemoryDataMessage: self._process_memory_data_message,
            MemoryDataBlockMessage: self._process_memory_data_block_message,
            # Status messages
            BusErrorCounterStatusMessage: self._handle_bus_error_counter,
            RelayStatusMessage: self._handle_relay_status,
            RelayStatusMessage2: self._handle_relay_status,
            RelayStatusMessage3: self._handle_relay_status3,
            ForcedOn: self._handle_forced_on,
            ForcedOff: self._handle_forced_off,
            Inhibit: self._handle_inhibit,
            CancelForcedOn: self._handle_cancel_forced,
            CancelForcedOff: self._handle_cancel_forced,
            CancelInhibit: self._handle_cancel_forced,
            # Temperature messages
            SensorTemperatureMessage: self._handle_sensor_temperature,
            TempSensorStatusMessage: self._handle_temp_sensor_status,
            TempSensorSettingsPart1: self._handle_temp_sensor_settings,
            TempSensorSettingsPart2: self._handle_temp_sensor_settings,
            TempSensorSettingsPart3: self._handle_temp_sensor_settings,
            TempSensorSettingsPart4: self._handle_temp_sensor_settings,
            # Button and module status messages
            PushButtonStatusMessage: self._handle_push_button_status,
            ModuleStatusMessage: self._handle_module_status,
            ModuleStatusMessage2: self._handle_module_status2,
            CounterStatusMessage: self._handle_counter_status,
            ModuleStatusPirMessage: self._handle_module_status_pir,
            ModuleStatusGP4PirMessage: self._handle_module_status_gp4_pir,
            # LED messages
            UpdateLedStatusMessage: self._handle_led_status,
            SetLedMessage: self._handle_set_led,
            ClearLedMessage: self._handle_clear_led,
            SlowBlinkingLedMessage: self._handle_slow_blinking_led,
            FastBlinkingLedMessage: self._handle_fast_blinking_led,
            # Dimmer and blind messages
            DimmerChannelStatusMessage: self._handle_dimmer_status,
            DimmerStatusMessage: self._handle_dimmer_status,
            SliderStatusMessage: self._handle_slider_status,
            BlindStatusNgMessage: self._handle_blind_status_ng,
            BlindStatusNg20Message: self._handle_blind_status_ng20,
            BlindStatusMessage: self._handle_blind_status,
            CoverPosMessage: self._handle_cover_position,
            # Sensor messages
            MeteoRawMessage: self._handle_meteo_raw,
            SensorRawMessage: self._handle_sensor_raw,
            CounterValueMessage: self._handle_counter_value,
            DimValueStatus: self._handle_dim_value_status,
            # PSU messages
            PsuLoadMessage: self._handle_psu_load,
            PsuValuesMessage: self._handle_psu_values,
        }

    async def _handle_channel_name_part1(
        self, message: ChannelNamePart1Message
    ) -> None:
        """Handle channel name part 1 messages."""
        await self._process_channel_name_message(1, message)
        await self._cache()

    async def _handle_channel_name_part2(
        self, message: ChannelNamePart2Message
    ) -> None:
        """Handle channel name part 2 messages."""
        await self._process_channel_name_message(2, message)
        await self._cache()

    async def _handle_channel_name_part3(
        self, message: ChannelNamePart3Message
    ) -> None:
        """Handle channel name part 3 messages."""
        await self._process_channel_name_message(3, message)
        await self._cache()

    async def _handle_bus_error_counter(
        self, message: BusErrorCounterStatusMessage
    ) -> None:
        """Handle bus error counter status messages."""
        await self._update_property(
            "bus_error_tx", {"cur": message.transmit_error_counter}
        )
        await self._update_property(
            "bus_error_rx", {"cur": message.receive_error_counter}
        )
        await self._update_property("bus_error_off", {"cur": message.bus_off_counter})

    async def _handle_relay_status(
        self, message: RelayStatusMessage | RelayStatusMessage2
    ) -> None:
        """Handle relay status messages."""
        await self._update_channel(
            message.channel,
            {
                "on": message.is_on(),
                "inhibit": message.is_inhibited(),
                "forced_on": message.is_forced_on(),
                "disabled": message.is_disabled(),
            },
        )

    async def _handle_relay_status3(self, message: RelayStatusMessage3) -> None:
        """Handle relay status 3 messages."""
        for channel in range(1, 9):
            await self._update_channel(
                channel,
                {
                    "on": message.is_on(channel),
                    "inhibit": message.is_inhibited(channel),
                    "forced_on": message.is_forced_on(channel),
                    "forced_off": message.is_forced_off(channel),
                    "disabled": message.is_program_disabled(channel),
                },
            )

    async def _handle_forced_on(self, message: ForcedOn) -> None:
        """Handle forced on messages."""
        await self._update_channel(
            message.channel,
            {"forced_on": True, "forced_off": False, "inhibit": False},
        )

    async def _handle_forced_off(self, message: ForcedOff) -> None:
        """Handle forced off messages."""
        await self._update_channel(
            message.channel,
            {"forced_on": False, "forced_off": True, "inhibit": False},
        )

    async def _handle_inhibit(self, message: Inhibit) -> None:
        """Handle inhibit messages."""
        await self._update_channel(
            message.channel,
            {"forced_on": False, "forced_off": False, "inhibit": True},
        )

    async def _handle_cancel_forced(
        self, message: CancelForcedOn | CancelForcedOff | CancelInhibit
    ) -> None:
        """Handle cancel forced/inhibit messages."""
        await self._update_channel(
            message.channel,
            {"forced_on": False, "forced_off": False, "inhibit": False},
        )

    async def _handle_sensor_temperature(
        self, message: SensorTemperatureMessage
    ) -> None:
        """Handle sensor temperature messages."""
        chan = self._translate_channel_name(self._data["TemperatureChannel"])
        temp_channel = self._channels.get(chan)
        if isinstance(temp_channel, TemperatureChannelType):
            await temp_channel.maybe_update_temperature(message.getCurTemp(), 1 / 64)
        await self._update_channel(
            chan,
            {
                "min": message.getMinTemp(),
                "max": message.getMaxTemp(),
            },
        )

    async def _handle_temp_sensor_settings(
        self,
        message: (
            TempSensorSettingsPart1
            | TempSensorSettingsPart2
            | TempSensorSettingsPart3
            | TempSensorSettingsPart4
        ),
    ) -> None:
        """Handle temperature sensor settings Part1-4 replies."""
        if self._temp_settings is not None:
            self._temp_settings.feed_message(message)

    async def _handle_temp_sensor_status(
        self, message: TempSensorStatusMessage
    ) -> None:
        """Handle temperature sensor status messages."""
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
            temp_channel = self._channels[chan]
            if isinstance(temp_channel, TemperatureChannelType):
                await temp_channel.maybe_update_temperature(message.current_temp, 1 / 2)

        # Update thermostat channels.
        # The spec channel names differ between module generations: the older
        # modules (VMBEL1/2/4, VMBGP*, VMBGPO, ...) use the short names
        # ("Boost", "Alarm 1"), while the "-20" variants use the long names
        # ("Boost heater/cooler", "Temperature alarm 1"). Map both so the
        # boost/alarm binary sensors stay in sync on every module.
        channel_name_to_msg_prop_map = {
            "Heater": "heater",
            "Boost": "boost",
            "Boost heater/cooler": "boost",
            "Pump": "pump",
            "Cooler": "cooler",
            "Alarm 1": "alarm1",
            "Alarm 2": "alarm2",
            "Alarm 3": "alarm3",
            "Alarm 4": "alarm4",
            "Temperature alarm 1": "alarm1",
            "Temperature alarm 2": "alarm2",
            "Temperature alarm 3": "alarm3",
            "Temperature alarm 4": "alarm4",
        }
        for channel_str in self._data["Channels"]:
            if (
                keys_exists(self._data, "Channels", channel_str, "Type")
                and self._data["Channels"][channel_str]["Type"] == "ThermostatChannel"
            ):
                channel = self._translate_channel_name(channel_str)
                channel_name = self._data["Channels"][channel_str]["Name"]
                if (
                    channel in self._channels
                    and channel_name in channel_name_to_msg_prop_map
                ):
                    await self._update_channel(
                        channel,
                        {
                            "closed": getattr(
                                message, channel_name_to_msg_prop_map[channel_name]
                            )
                        },
                    )

    async def _handle_push_button_status(
        self, message: PushButtonStatusMessage, channel_offset: int
    ) -> None:
        """Handle push button status messages."""
        _update_buttons = False
        for channel_types in self._data["Channels"]:
            if keys_exists(
                self._data, "Channels", channel_types, "Type"
            ) and self._data["Channels"][channel_types]["Type"] in (
                "Button",
                "Sensor",
                "ButtonCounter",
                "Relay",
            ):
                _update_buttons = True
                break
        if _update_buttons:
            for channel_id in range(1, 9):
                channel = self._translate_channel_name(channel_id + channel_offset)
                if channel_id in message.closed:
                    await self._update_channel(channel, {"closed": True, "on": True})
                if channel_id in message.closed_long:
                    await self._update_channel(channel, {"long": True})
                if channel_id in message.opened:
                    await self._update_channel(
                        channel, {"closed": False, "long": False, "on": False}
                    )

    async def _handle_module_status(
        self, message: ModuleStatusMessage, channel_offset: int
    ) -> None:
        """Handle module status messages."""
        for channel_id in range(1, 9):
            channel = self._translate_channel_name(channel_id + channel_offset)
            if channel_id in message.closed:
                await self._update_channel(channel, {"closed": True})
            elif channel in self._channels and isinstance(
                self._channels[channel], (Button, ButtonCounter)
            ):
                await self._update_channel(channel, {"closed": False})

    async def _handle_module_status2(
        self, message: ModuleStatusMessage2, channel_offset: int
    ) -> None:
        """Handle module status 2 messages."""
        for channel_id in range(1, 9):
            channel = self._translate_channel_name(channel_id + channel_offset)
            if channel_id in message.closed:
                await self._update_channel(channel, {"closed": True})
            elif channel in self._channels and isinstance(
                self._channels[channel], (Button, ButtonCounter)
            ):
                await self._update_channel(channel, {"closed": False})
            if channel_id in message.enabled:
                await self._update_channel(channel, {"enabled": True})
            elif channel in self._channels and isinstance(
                self._channels[channel], (Button, ButtonCounter)
            ):
                await self._update_channel(channel, {"enabled": False})
        await self._update_property(
            "selected_program",
            {"selected_program_str": message.selected_program_str},
        )

    async def _handle_counter_status(self, message: CounterStatusMessage) -> None:
        """Handle counter status messages."""
        channel_num = self._translate_channel_name(message.channel)
        channel_obj = self._channels.get(channel_num)
        if not isinstance(channel_obj, ButtonCounter):
            return
        updates: dict[str, int | float] = {
            "pulses": message.pulses,
            "counter": message.counter,
            "delay": message.delay,
        }
        if not channel_obj.is_gas() and not channel_obj.is_water():
            updates["power"] = round(message.watt, 2)
        await self._update_channel(channel_num, updates)

    async def _handle_module_status_pir(self, message: ModuleStatusPirMessage) -> None:
        """Handle PIR module status messages."""
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
        await self._update_property(
            "selected_program",
            {"selected_program_str": message.selected_program_str},
        )

    async def _handle_module_status_gp4_pir(
        self, message: ModuleStatusGP4PirMessage, channel_offset: int
    ) -> None:
        """Handle GP4 PIR module status messages."""
        await self._update_property("light_value", {"cur": message.light_value})
        for channel_id in range(1, 9):
            channel = self._translate_channel_name(channel_id + channel_offset)
            await self._update_channel(
                channel, {"closed": channel_id in message.closed}
            )
            channel_obj = self._channels.get(channel)
            if isinstance(channel_obj, Button) and not isinstance(channel_obj, Sensor):
                await self._update_channel(
                    channel, {"enabled": channel_id in message.enabled}
                )
        await self._update_property(
            "selected_program",
            {"selected_program_str": message.selected_program_str},
        )

    async def _handle_led_status(
        self, message: UpdateLedStatusMessage, channel_offset: int
    ) -> None:
        """Handle LED status update messages."""
        for channel_id in range(1, 9):
            channel = self._translate_channel_name(channel_id + channel_offset)
            if channel_id in message.led_slow_blinking:
                await self._update_channel(channel, {"led_state": "slow"})
            elif channel_id in message.led_fast_blinking:
                await self._update_channel(channel, {"led_state": "fast"})
            elif channel_id in message.led_on:
                await self._update_channel(channel, {"led_state": "on"})
            else:
                await self._update_channel(channel, {"led_state": "off"})

    async def _handle_set_led(
        self, message: SetLedMessage, channel_offset: int
    ) -> None:
        """Handle set LED messages."""
        for channel_id in range(1, 9):
            channel = self._translate_channel_name(channel_id + channel_offset)
            if channel_id in message.leds:
                await self._update_channel(channel, {"led_state": "on"})

    async def _handle_clear_led(
        self, message: ClearLedMessage, channel_offset: int
    ) -> None:
        """Handle clear LED messages."""
        for channel_id in range(1, 9):
            channel = self._translate_channel_name(channel_id + channel_offset)
            if channel_id in message.leds:
                await self._update_channel(channel, {"led_state": "off"})

    async def _handle_slow_blinking_led(
        self, message: SlowBlinkingLedMessage, channel_offset: int
    ) -> None:
        """Handle slow blinking LED messages."""
        for channel_id in range(1, 9):
            channel = self._translate_channel_name(channel_id + channel_offset)
            if channel_id in message.leds:
                await self._update_channel(channel, {"led_state": "slow"})

    async def _handle_fast_blinking_led(
        self, message: FastBlinkingLedMessage, channel_offset: int
    ) -> None:
        """Handle fast blinking LED messages."""
        for channel_id in range(1, 9):
            channel = self._translate_channel_name(channel_id + channel_offset)
            if channel_id in message.leds:
                await self._update_channel(channel, {"led_state": "fast"})

    async def _handle_dimmer_status(
        self, message: DimmerChannelStatusMessage | DimmerStatusMessage
    ) -> None:
        """Handle dimmer status messages."""
        channel = self._translate_channel_name(message.channel)
        await self._update_channel(channel, {"state": message.cur_dimmer_state()})

    async def _handle_slider_status(self, message: SliderStatusMessage) -> None:
        """Handle slider status messages."""
        channel = self._translate_channel_name(message.channel)
        await self._update_channel(channel, {"state": message.cur_slider_state()})

    async def _handle_blind_status_ng(self, message: BlindStatusNgMessage) -> None:
        """Handle blind status NG messages."""
        channel = self._translate_channel_name(message.channel)
        await self._update_channel(
            channel, {"state": message.status, "position": message.position}
        )

    async def _handle_blind_status_ng20(self, message: BlindStatusNg20Message) -> None:
        """Handle blind status NG20 messages."""
        # The messages contain the status for both channels, so we need to update both channels
        for i in range(2):
            channel = self._translate_channel_name(message.channel[i])
            await self._update_channel(
                channel, {"state": message.status[i], "position": message.position[i]}
            )

    async def _handle_blind_status(self, message: BlindStatusMessage) -> None:
        """Handle blind status messages."""
        channel = self._translate_channel_name(message.channel)
        await self._update_channel(channel, {"state": message.status})

    async def _handle_cover_position(self, message: CoverPosMessage) -> None:
        """Handle cover position messages."""
        channel = self._translate_channel_name(message.channel)
        await self._update_channel(channel, {"position": message.position})

    async def _handle_meteo_raw(self, message: MeteoRawMessage) -> None:
        """Handle meteo raw messages."""
        await self._update_channel(11, {"cur": message.rain})
        await self._update_channel(12, {"cur": message.light})
        await self._update_channel(13, {"cur": message.wind})

    async def _handle_sensor_raw(self, message: SensorRawMessage) -> None:
        """Handle sensor raw messages."""
        await self._update_channel(
            message.sensor, {"cur": message.value, "unit": message.unit}
        )

    async def _handle_counter_value(self, message: CounterValueMessage) -> None:
        """Handle counter value messages."""
        await self._update_channel(
            message.channel, {"power": message.power, "energy": message.energy}
        )

    async def _handle_dim_value_status(self, message: DimValueStatus) -> None:
        """Handle dim value status messages."""
        for offset, dim_value in enumerate(message.dim_values):
            channel = message.channel + offset
            await self._update_channel(channel, {"state": dim_value})

    async def _handle_psu_load(self, message: PsuLoadMessage) -> None:
        """Handle PSU load messages."""
        await self._update_property("psu_load_out", {"cur": message.out})
        await self._update_property("psu_load_1", {"cur": message.load_1})
        await self._update_property("psu_load_2", {"cur": message.load_2})

    async def _handle_psu_values(self, message: PsuValuesMessage) -> None:
        """Handle PSU values messages."""
        suffix = "out" if message.channel == 3 else f"{message.channel}"
        await self._update_property(f"psu_power_{suffix}", {"cur": message.watt})
        await self._update_property(f"psu_voltage_{suffix}", {"cur": message.volt})
        await self._update_property(f"psu_current_{suffix}", {"cur": message.amp})

    async def on_message(self, message: Message) -> None:
        """Process received message."""
        self._log.debug(f"RX: {message}")
        _channel_offset = self.calc_channel_offset(message.address)

        # Use dispatch table for message handling
        handler = self._message_handlers.get(type(message))
        if handler:
            # Check if handler needs channel_offset parameter
            sig = inspect.signature(handler)
            if "channel_offset" in sig.parameters:
                await handler(message, _channel_offset)
            else:
                await handler(message)

        # Notify status
        self._got_status.set()

    async def _update_channel(self, channel: int, updates: dict[str, Any]) -> None:
        try:
            await self._channels[channel].update(updates)
        except KeyError:
            self._log.error(
                f"channel {channel} does not exist for module @ address {self}"
            )

    async def _update_property(
        self, property_name: str, updates: dict[str, Any]
    ) -> None:
        try:
            await self._properties[property_name].update(updates)
        except KeyError:
            self._log.error(
                f"property {property_name} does not exist for module @ address {self}"
            )

    async def _process_memory_data_block_message(
        self, message: MemoryDataBlockMessage
    ) -> None:
        if self._memory is not None:
            self._memory.feed_message(message)
        addr = f"{message.high_address:02X}{message.low_address:02X}"
        if "Memory" not in self._data:
            return
        # TODO this can also be SensorName, implement that also
        if "ModuleName" not in self._data["Memory"]:
            return
        addr_data = self._data["Memory"]["ModuleName"]
        if isinstance(self._name, str):
            # Name already fully assembled, nothing to do
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
                # Calculate the byte position within the overall module name
                position_in_range = incoming_addr - start_addr
                base_position = range_byte_offset + position_in_range
                # Store each byte in the temporary buffer, not in _name itself.
                # _name is only set to a string once all bytes have been received.
                for i, byte_val in enumerate(message.data):
                    char_position = base_position + i
                    self._name_buffer[char_position] = chr(byte_val)
                # Check if all expected bytes have been received
                total_bytes = ranges[-1][2] + (ranges[-1][1] - ranges[-1][0] + 1)
                if len(self._name_buffer) >= total_bytes:
                    # All bytes received: assemble the name string, skip 0xFF (unprogrammed bytes)
                    self._name = "".join(
                        str(x) for x in self._name_buffer.values() if x != chr(0xFF)
                    )
                    self._name_buffer = {}  # release buffer
                    await self._cache()
                break

    async def _process_memory_data_message(self, message: MemoryDataMessage) -> None:
        if self._memory is not None:
            self._memory.feed_message(message)
        addr_int = join_address(message.high_address, message.low_address)
        addr = f"{message.high_address:02X}{message.low_address:02X}"
        if "Memory" not in self._data:
            return
        if "Address" not in self._data["Memory"]:
            return
        if addr not in self._data["Memory"]["Address"]:
            return
        mdata = self._data["Memory"]["Address"][addr]
        if "Match" in mdata:
            for chan, chan_data in handle_match(mdata["Match"], message.data).items():
                data = chan_data.copy()
                # Special handling for 16-bit PulsePerUnits
                if "PulsePerUnits" in data:
                    current_pulses = getattr(self._channels[chan], "_pulses", 0) or 0
                    # If this is the high byte (even address in VMB8IN)
                    if addr_int % 4 == 0:  # 02E8, 02EC...
                        new_pulses = (message.data << 8) + (current_pulses & 0xFF)
                    else:  # 02E9, 02ED...
                        new_pulses = (current_pulses & 0xFF00) + message.data
                    data["pulses"] = new_pulses
                await self._update_channel(chan, data)

    async def _process_channel_name_message(
        self,
        part: int,
        message: ChannelNamePart1Message
        | ChannelNamePart2Message
        | ChannelNamePart3Message,
    ) -> None:
        channel = self._translate_channel_name(message.channel)
        if channel not in self._channels:
            return
        if self._channels[channel].set_name_part(part, message.name) and self.loaded:
            await self._channels[channel].status_update()

    def _translate_channel_name(self, channel: str | int) -> int:
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
