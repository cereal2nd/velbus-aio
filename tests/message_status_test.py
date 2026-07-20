"""Unit tests for the status/report message classes."""

from __future__ import annotations

import json

import pytest

from velbusaio.const import PRIORITY_HIGH, PRIORITY_LOW
from velbusaio.message import ParserError
from velbusaio.messages.blind_status import (
    BlindStatusMessage,
    BlindStatusNg20Message,
    BlindStatusNgMessage,
)
from velbusaio.messages.bus_error_counter_status import BusErrorCounterStatusMessage
from velbusaio.messages.counter_status import CounterStatusMessage
from velbusaio.messages.counter_value import CounterValueMessage
from velbusaio.messages.dali_dim_value_status import DimValueStatus
from velbusaio.messages.dimmer_channel_status import DimmerChannelStatusMessage
from velbusaio.messages.dimmer_status import DimmerStatusMessage
from velbusaio.messages.ir_receiver_status import IRReceiverStatusMessage
from velbusaio.messages.kwh_status import KwhStatusMessage
from velbusaio.messages.module_status import (
    ModuleStatusGP4PirMessage,
    ModuleStatusMessage,
    ModuleStatusMessage2,
    ModuleStatusPirMessage,
)
from velbusaio.messages.psu_load import PsuLoadMessage
from velbusaio.messages.psu_values import PsuValuesMessage
from velbusaio.messages.push_button_status import PushButtonStatusMessage
from velbusaio.messages.relay_status import (
    RelayStatusMessage,
    RelayStatusMessage2,
    RelayStatusMessage3,
)
from velbusaio.messages.slider_status import SliderStatusMessage
from velbusaio.messages.temp_sensor_status import TempSensorStatusMessage


class TestBlindStatusNgMessage:
    """Tests for BlindStatusNgMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = BlindStatusNgMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x05, 0x02, 0x00, 0x40, 0, 0])
        )
        assert msg.channel == 1
        assert msg.timeout == 5
        assert msg.status == 2
        assert msg.position == 0x40
        assert msg.is_moving_down()
        assert not msg.is_moving_up()
        assert not msg.is_stopped()

    def test_to_json(self):
        """Test To json."""
        msg = BlindStatusNgMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x00, 0x01, 0x00, 0x00, 0, 0])
        )
        result = json.loads(msg.to_json())
        assert result["channel"] == 1
        assert result["status"] == "up"

    def test_needs_data(self):
        """Test Needs data."""
        msg = BlindStatusNgMessage()
        with pytest.raises(ParserError):
            msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]))


class TestBlindStatusNg20Message:
    """Tests for BlindStatusNg20Message."""

    def test_populate(self):
        """Test Populate."""
        msg = BlindStatusNg20Message()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x21, 50, 80, 0, 0, 0, 0]))
        assert msg.channel == (1, 2)
        assert msg.status == (1, 2)
        assert msg.position == (50, 80)

    def test_to_json(self):
        """Test To json."""
        msg = BlindStatusNg20Message()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x21, 50, 80, 0, 0, 0, 0]))
        result = json.loads(msg.to_json())
        assert result["status"] == ["up", "down"]


class TestBlindStatusMessage:
    """Tests for BlindStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = BlindStatusMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x02, 5, 0x01, 0, 0, 0, 0]))
        assert msg.channel == 1
        assert msg.timeout == 5
        assert msg.status == 1
        assert msg.is_moving_up()


class TestModuleStatusMessage:
    """Tests for ModuleStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ModuleStatusMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x04, 0x08]))
        assert msg.closed == [1]
        assert msg.led_on == [2]
        assert msg.led_slow_blinking == [3]
        assert msg.led_fast_blinking == [4]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ModuleStatusMessage()
        msg.closed = [1]
        msg.led_on = [2]
        msg.led_slow_blinking = [3]
        msg.led_fast_blinking = [4]
        assert msg.data_to_binary() == bytes([0xED, 0x01, 0x02, 0x04, 0x08])


class TestModuleStatusMessage2:
    """Tests for ModuleStatusMessage2."""

    def test_populate(self):
        """Test Populate."""
        msg = ModuleStatusMessage2()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x04, 0x08, 0x10, 0x01])
        )
        assert msg.closed == [1]
        assert msg.enabled == [2]
        assert msg.normal == [3]
        assert msg.locked == [4]
        assert msg.programenabled == [5]
        assert msg.selected_program == 1
        assert msg.selected_program_str == "summer"

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ModuleStatusMessage2()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x04, 0x08, 0x10, 0x01])
        )
        assert msg.data_to_binary() == bytes([0xED, 0x01, 0x02, 0x04, 0x08])


class TestModuleStatusPirMessage:
    """Tests for ModuleStatusPirMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ModuleStatusPirMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x03, 0x01, 0x02, 0, 0, 0x01, 0])
        )
        assert msg.dark is True
        assert msg.light is True
        assert msg.motion1 is False
        assert msg.light_value == (0x01 << 8) + 0x02
        assert msg.selected_program == 1

    def test_data_to_binary_not_implemented(self):
        """Test Data to binary not implemented."""
        msg = ModuleStatusPirMessage()
        with pytest.raises(NotImplementedError):
            msg.data_to_binary()


class TestModuleStatusGP4PirMessage:
    """Tests for ModuleStatusGP4PirMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ModuleStatusGP4PirMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x03, 0x04, 0x08, 0x02, 0x0A])
        )
        assert msg.closed == [1]
        assert msg.enabled == [2]
        assert msg.locked == [3]
        assert msg.selected_program == 2
        assert msg.light_value_send_interval == 0x0A

    def test_data_to_binary_not_implemented(self):
        """Test Data to binary not implemented."""
        msg = ModuleStatusGP4PirMessage()
        with pytest.raises(NotImplementedError):
            msg.data_to_binary()


class TestRelayStatusMessage:
    """Tests for RelayStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = RelayStatusMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x00, 0x01, 0x00, 0, 0, 5])
        )
        assert msg.channel == 1
        assert msg.is_normal()
        assert msg.is_on()
        assert msg.delay_time == 5

    def test_state_helpers(self):
        """Test State helpers."""
        msg = RelayStatusMessage()
        msg.disable_inhibit_forced = 0x01
        assert msg.is_inhibited()
        msg.disable_inhibit_forced = 0x02
        assert msg.is_forced_on()
        msg.disable_inhibit_forced = 0x03
        assert msg.is_disabled()
        msg.status = 0x03
        assert msg.has_interval_timer_on()

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = RelayStatusMessage()
        msg.channel = 1
        msg.status = 1
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0xFB, 0x01, 0x00, 0x01, 0x00, 0, 0, 5])


class TestRelayStatusMessage2:
    """Tests for RelayStatusMessage2 (VMB4RY)."""

    def test_is_on_bitmask(self):
        """Test Is on bitmask."""
        msg = RelayStatusMessage2()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x00, 0x01, 0x00, 0, 0, 0])
        )
        assert msg.is_on()


class TestRelayStatusMessage3:
    """Tests for RelayStatusMessage3 (VMB4RYLD-20)."""

    def test_populate(self):
        """Test Populate."""
        msg = RelayStatusMessage3()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x05, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40])
        )
        assert msg.is_on(1)
        assert msg.is_on(3)
        assert not msg.is_on(2)
        assert msg.is_inhibited(2)
        assert msg.is_forced_on(3)
        assert msg.is_forced_off(4)
        assert msg.is_program_disabled(5)
        assert msg.has_interval_timer_on(6)


class TestDimmerStatusMessage:
    """Tests for DimmerStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = DimmerStatusMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x02, 0x64, 0x00, 0, 0, 0, 0x01])
        )
        assert msg.dimmer_mode == 0x02
        assert msg.is_dimmer()
        assert msg.cur_dimmer_state() == 100
        assert msg.dimmer_config == 1

    def test_mode_helpers(self):
        """Test Mode helpers."""
        msg = DimmerStatusMessage()
        msg.dimmer_mode = 0x00
        assert msg.is_start_stop()
        msg.dimmer_mode = 0x01
        assert msg.is_staircase()
        msg.dimmer_mode = 0x03
        assert msg.is_dimmer_memory()
        msg.dimmer_mode = 0x04
        assert msg.is_multi()
        msg.dimmer_mode = 0x05
        assert msg.is_slow_on()
        msg.dimmer_mode = 0x06
        assert msg.is_slow()
        assert msg.is_slow_off()

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = DimmerStatusMessage()
        msg.dimmer_mode = 0x02
        msg.dimmer_state = 100
        msg.delay_time = 1
        assert msg.data_to_binary() == bytes([0xEE, 0x02, 100, 0x00, 0, 0, 1])


class TestDimmerChannelStatusMessage:
    """Tests for DimmerChannelStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = DimmerChannelStatusMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x00, 0x64, 0x00, 0, 0, 2])
        )
        assert msg.channel == 1
        assert msg.is_normal()
        assert msg.cur_dimmer_state() == 100
        assert msg.delay_time == 2

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = DimmerChannelStatusMessage()
        msg.channel = 1
        msg.dimmer_state = 100
        msg.delay_time = 2
        assert msg.data_to_binary() == bytes([0xB8, 0x01, 0x00, 100, 0x00, 0, 0, 2])


class TestSliderStatusMessage:
    """Tests for SliderStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SliderStatusMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 0x50, 0x00]))
        assert msg.channel == 1
        assert msg.cur_slider_state() == 0x50
        assert msg.slider_long_pressed == 0

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SliderStatusMessage()
        msg.channel = 1
        msg.slider_state = 0x50
        assert msg.data_to_binary() == bytes([0x0F, 0x01, 0x50, 0x00])


class TestTempSensorStatusMessage:
    """Tests for TempSensorStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = TempSensorStatusMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x00, 0x00, 0x00, 0x2A, 0x28, 0x00, 0x00])
        )
        assert msg.status_str == "run"
        assert msg.mode_str == "safe"
        assert msg.getCurTemp() == 21.0
        assert msg.target_temp == 20.0
        assert msg.sleep_timer == 0

    def test_to_json(self):
        """Test To json."""
        msg = TempSensorStatusMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x00, 0x00, 0x01, 0x2A, 0x28, 0x00, 0x00])
        )
        result = json.loads(msg.to_json())
        assert result["current_temp"] == 21.0
        assert result["heater"] is True


class TestPushButtonStatusMessage:
    """Tests for PushButtonStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = PushButtonStatusMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 0x02, 0x04]))
        assert msg.closed == [1]
        assert msg.opened == [2]
        assert msg.closed_long == [3]
        assert msg.get_channels() == [1, 2]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = PushButtonStatusMessage()
        msg.closed = [1]
        msg.opened = [2]
        msg.closed_long = [3]
        assert msg.data_to_binary() == bytes([0x00, 0x01, 0x02, 0x04])

    def test_default_high_priority(self):
        """Test Default high priority."""
        msg = PushButtonStatusMessage()
        assert msg.priority == PRIORITY_HIGH


class TestIRReceiverStatusMessage:
    """Tests for IRReceiverStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = IRReceiverStatusMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x04, 0x08]))
        assert msg.closed == [1]
        assert msg.led_on == [2]


class TestCounterStatusMessage:
    """Tests for CounterStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = CounterStatusMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05, 0, 0, 0, 100, 0, 10]))
        assert msg.channel == 2
        assert msg.pulses == 100
        assert msg.counter == 100
        assert msg.delay == 10
        assert msg.get_channels() == 2


class TestCounterValueMessage:
    """Tests for CounterValueMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = CounterValueMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x10, 0x00, 0x64, 0, 0, 0, 5]))
        assert msg.channel == 2
        assert msg.power == 100
        assert msg.energy == 5
        assert msg.get_channels() == 2


class TestKwhStatusMessage:
    """Tests for KwhStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = KwhStatusMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05, 0, 0, 0, 100, 0, 10]))
        assert msg.channel == 2
        assert msg.pulses == 100
        assert msg.counter == 100
        assert msg.kwh == 1.0
        assert msg.delay == 10
        assert msg.get_channels() == 2


class TestPsuLoadMessage:
    """Tests for PsuLoadMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = PsuLoadMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 50, 60, 70]))
        assert msg.mode == 1
        assert msg.load_1 == 50
        assert msg.load_2 == 60
        assert msg.out == 70


class TestPsuValuesMessage:
    """Tests for PsuValuesMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = PsuValuesMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x10, 0x00, 0x64, 0x00, 0xC8, 0x00, 0x0A])
        )
        assert msg.channel == 1
        assert msg.watt == 0.1
        assert msg.volt == 0.2
        assert msg.amp == 0.01


class TestBusErrorCounterStatusMessage:
    """Tests for BusErrorCounterStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = BusErrorCounterStatusMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([1, 2, 3]))
        assert msg.transmit_error_counter == 1
        assert msg.receive_error_counter == 2
        assert msg.bus_off_counter == 3

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = BusErrorCounterStatusMessage()
        msg.transmit_error_counter = 1
        msg.receive_error_counter = 2
        msg.bus_off_counter = 3
        assert msg.data_to_binary() == bytes([0xDA, 1, 2, 3])


class TestDimValueStatus:
    """Tests for DimValueStatus (Dali dim value status)."""

    def test_populate(self):
        """Test Populate."""
        msg = DimValueStatus()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05, 100, 50]))
        assert msg.channel == 5
        assert msg.dim_values == [100, 50]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = DimValueStatus()
        msg.channel = 5
        msg.dim_values = [100, 50]
        assert msg.data_to_binary() == bytes([0xA5, 0x05, 100, 50])
