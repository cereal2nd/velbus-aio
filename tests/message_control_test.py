"""Unit tests for the control/actuation message classes."""

from __future__ import annotations

import pytest

from velbusaio.const import PRIORITY_HIGH, PRIORITY_LOW
from velbusaio.message import ParserError
from velbusaio.messages.cancel_forced_off import CancelForcedOff
from velbusaio.messages.cancel_forced_on import CancelForcedOn
from velbusaio.messages.cancel_inhibit import CancelInhibit
from velbusaio.messages.clear_led import ClearLedMessage
from velbusaio.messages.cover_down import CoverDownMessage, CoverDownMessage2
from velbusaio.messages.cover_off import CoverOffMessage, CoverOffMessage2
from velbusaio.messages.cover_position import CoverPosMessage
from velbusaio.messages.cover_up import CoverUpMessage, CoverUpMessage2
from velbusaio.messages.fast_blinking_led import FastBlinkingLedMessage
from velbusaio.messages.forced_off import ForcedOff
from velbusaio.messages.forced_on import ForcedOn
from velbusaio.messages.inhibit import Inhibit
from velbusaio.messages.restore_dimmer import (
    RestoreDimmerMessage,
    RestoreDimmerMessage2,
)
from velbusaio.messages.set_dimmer import SetDimmerMessage, SetDimmerMessage2
from velbusaio.messages.set_led import SetLedMessage
from velbusaio.messages.slow_blinking_led import SlowBlinkingLedMessage
from velbusaio.messages.start_relay_blinking_timer import StartRelayBlinkingTimerMessage
from velbusaio.messages.start_relay_timer import StartRelayTimerMessage
from velbusaio.messages.switch_relay_off import (
    SwitchRelayOffMessage,
    SwitchRelayOffMessage20,
)
from velbusaio.messages.switch_relay_on import (
    SwitchRelayOnMessage,
    SwitchRelayOnMessage20,
)
from velbusaio.messages.update_led_status import UpdateLedStatusMessage
from velbusaio.messages.very_fast_blinking_led import VeryFastBlinkingLedMessage


class TestCoverOffMessage:
    """Tests for CoverOffMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = CoverOffMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01]))
        assert msg.channel == 1
        assert msg.priority == PRIORITY_HIGH

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CoverOffMessage()
        msg.channel = 1
        assert msg.data_to_binary() == bytes([0x04, 0x01])

    def test_needs_high_priority(self):
        """Test Needs high priority."""
        msg = CoverOffMessage()
        with pytest.raises(ParserError):
            msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]))


class TestCoverOffMessage2:
    """Tests for CoverOffMessage2 (VMB1BL/VMB2BL)."""

    def test_populate(self):
        """Test Populate."""
        msg = CoverOffMessage2()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x02]))
        assert msg.channel == 1

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CoverOffMessage2()
        msg.channel = 1
        assert msg.data_to_binary() == bytes([0x04, 0x03])
        msg.channel = 2
        assert msg.data_to_binary() == bytes([0x04, 0x0C])


class TestCoverUpMessage:
    """Tests for CoverUpMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = CoverUpMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 0, 0, 5]))
        assert msg.channel == 1
        assert msg.delay_time == 5

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CoverUpMessage()
        msg.channel = 1
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x05, 0x01, 0, 0, 5])


class TestCoverUpMessage2:
    """Tests for CoverUpMessage2."""

    def test_populate(self):
        """Test Populate."""
        msg = CoverUpMessage2()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x02, 0, 0, 5]))
        assert msg.channel == 1
        assert msg.delay_time == 5

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CoverUpMessage2()
        msg.channel = 1
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x05, 0x03, 0, 0, 5])


class TestCoverDownMessage:
    """Tests for CoverDownMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = CoverDownMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 0, 0, 5]))
        assert msg.channel == 1
        assert msg.delay_time == 5

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CoverDownMessage()
        msg.channel = 1
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x06, 0x01, 0, 0, 5])


class TestCoverDownMessage2:
    """Tests for CoverDownMessage2."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CoverDownMessage2()
        msg.channel = 2
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x06, 0x0C, 0, 0, 5])


class TestCoverPosMessage:
    """Tests for CoverPosMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = CoverPosMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 50]))
        assert msg.channel == 1
        assert msg.position == 50

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CoverPosMessage()
        msg.channel = 1
        msg.position = 50
        assert msg.data_to_binary() == bytes([0x1C, 0x01, 50])


class TestSwitchRelayOffMessage:
    """Tests for SwitchRelayOffMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SwitchRelayOffMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x03]))
        assert msg.relay_channels == [1, 2]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SwitchRelayOffMessage()
        msg.relay_channels = [1, 2]
        assert msg.data_to_binary() == bytes([0x01, 0x03])


class TestSwitchRelayOffMessage20:
    """Tests for SwitchRelayOffMessage20."""

    def test_data_to_binary_channel_index(self):
        """Test Data to binary channel index."""
        msg = SwitchRelayOffMessage20()
        msg.relay_channels = [3]
        assert msg.data_to_binary() == bytes([0x01, 3])

    def test_data_to_binary_empty(self):
        """Test Data to binary empty."""
        msg = SwitchRelayOffMessage20()
        msg.relay_channels = []
        assert msg.data_to_binary() == bytes([0x01, 0])


class TestSwitchRelayOnMessage:
    """Tests for SwitchRelayOnMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SwitchRelayOnMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x03]))
        assert msg.relay_channels == [1, 2]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SwitchRelayOnMessage()
        msg.relay_channels = [1, 2]
        assert msg.data_to_binary() == bytes([0x02, 0x03])


class TestSwitchRelayOnMessage20:
    """Tests for SwitchRelayOnMessage20."""

    def test_data_to_binary_channel_index(self):
        """Test Data to binary channel index."""
        msg = SwitchRelayOnMessage20()
        msg.relay_channels = [3]
        assert msg.data_to_binary() == bytes([0x02, 3])

    def test_data_to_binary_empty(self):
        """Test Data to binary empty."""
        msg = SwitchRelayOnMessage20()
        msg.relay_channels = []
        assert msg.data_to_binary() == bytes([0x02, 0])


class TestSetDimmerMessage:
    """Tests for SetDimmerMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SetDimmerMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 100, 5, 0]))
        assert msg.dimmer_channels == [1]
        assert msg.dimmer_state == 100
        assert msg.dimmer_transitiontime == 5

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SetDimmerMessage()
        msg.dimmer_channels = [1]
        msg.dimmer_state = 100
        msg.dimmer_transitiontime = 5
        assert msg.data_to_binary() == bytes([0x07, 0x01, 100, 0, 5])


class TestSetDimmerMessage2:
    """Tests for SetDimmerMessage2 (integer channel numbering)."""

    def test_populate(self):
        """Test Populate."""
        msg = SetDimmerMessage2()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x05, 100, 5, 0]))
        assert msg.dimmer_channels == [5]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SetDimmerMessage2()
        msg.dimmer_channels = [5]
        msg.dimmer_state = 100
        msg.dimmer_transitiontime = 5
        assert msg.data_to_binary() == bytes([0x07, 5, 100, 0, 5])

    def test_channels_to_byte_requires_one(self):
        """Test Channels to byte requires one."""
        msg = SetDimmerMessage2()
        with pytest.raises(ValueError):
            msg.channels_to_byte([1, 2])


class TestRestoreDimmerMessage:
    """Tests for RestoreDimmerMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = RestoreDimmerMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 0x00, 0x05, 0x00]))
        assert msg.dimmer_channels == [1]
        assert msg.dimmer_transitiontime == 5

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = RestoreDimmerMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 0x00, 0x05, 0x00]))
        assert msg.data_to_binary() == bytes([0x11, 0x01, 0, 0, 5])


class TestRestoreDimmerMessage2:
    """Tests for RestoreDimmerMessage2 (integer channel numbering)."""

    def test_populate(self):
        """Test Populate."""
        msg = RestoreDimmerMessage2()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x05, 0x00, 0x05, 0x00]))
        assert msg.dimmer_channels == [5]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = RestoreDimmerMessage2()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x05, 0x00, 0x05, 0x00]))
        assert msg.data_to_binary() == bytes([0x11, 5, 0, 0, 5])


class TestStartRelayTimerMessage:
    """Tests for StartRelayTimerMessage."""

    def test_default_priority(self):
        """Test Default priority."""
        msg = StartRelayTimerMessage(0x01)
        assert msg.priority == PRIORITY_HIGH
        assert msg.rtr is False

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = StartRelayTimerMessage()
        msg.relay_channels = [1]
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x03, 0x01, 0, 0, 5])


class TestStartRelayBlinkingTimerMessage:
    """Tests for StartRelayBlinkingTimerMessage."""

    def test_default_priority(self):
        """Test Default priority."""
        msg = StartRelayBlinkingTimerMessage(0x01)
        assert msg.priority == PRIORITY_HIGH

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = StartRelayBlinkingTimerMessage()
        msg.relay_channels = [1]
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x0D, 0x01, 0, 0, 5])


class TestForcedOff:
    """Tests for ForcedOff."""

    def test_populate(self):
        """Test Populate."""
        msg = ForcedOff()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 0x00, 0x00, 0x05]))
        assert msg.channel == 1
        assert msg.delay_time == 5

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ForcedOff()
        msg.channel = 1
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x12, 0x01, 0, 0, 5])

    def test_default_high_priority(self):
        """Test Default high priority."""
        assert ForcedOff().priority == PRIORITY_HIGH


class TestForcedOn:
    """Tests for ForcedOn."""

    def test_populate(self):
        """Test Populate."""
        msg = ForcedOn()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x02, 0x00, 0x01, 0x00]))
        assert msg.channel == 2
        assert msg.delay_time == 0x0100

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ForcedOn()
        msg.channel = 1
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x14, 0x01, 0, 0, 5])


class TestInhibit:
    """Tests for Inhibit."""

    def test_populate(self):
        """Test Populate."""
        msg = Inhibit()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x01, 0x00, 0x00, 0x05]))
        assert msg.channel == 1
        assert msg.delay_time == 5

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = Inhibit()
        msg.channel = 1
        msg.delay_time = 5
        assert msg.data_to_binary() == bytes([0x16, 0x01, 0, 0, 5])


class TestCancelForcedOff:
    """Tests for CancelForcedOff."""

    def test_populate(self):
        """Test Populate."""
        msg = CancelForcedOff()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([0x02]))
        assert msg.channel == 2

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CancelForcedOff()
        msg.channel = 2
        assert msg.data_to_binary() == bytes([0x13, 2])


class TestCancelForcedOn:
    """Tests for CancelForcedOn."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CancelForcedOn()
        msg.channel = 2
        assert msg.data_to_binary() == bytes([0x15, 2])


class TestCancelInhibit:
    """Tests for CancelInhibit."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CancelInhibit()
        msg.channel = 2
        assert msg.data_to_binary() == bytes([0x17, 2])


class TestSetLedMessage:
    """Tests for SetLedMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SetLedMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x03]))
        assert msg.leds == [1, 2]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SetLedMessage()
        msg.leds = [1, 2]
        assert msg.data_to_binary() == bytes([0xF6, 0x03])


class TestClearLedMessage:
    """Tests for ClearLedMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ClearLedMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]))
        assert msg.leds == [1]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ClearLedMessage()
        msg.leds = [1]
        assert msg.data_to_binary() == bytes([0xF5, 0x01])


class TestFastBlinkingLedMessage:
    """Tests for FastBlinkingLedMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = FastBlinkingLedMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]))
        assert msg.leds == [1]
        assert msg.data_to_binary() == bytes([0xF8, 0x01])


class TestSlowBlinkingLedMessage:
    """Tests for SlowBlinkingLedMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SlowBlinkingLedMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]))
        assert msg.leds == [1]
        assert msg.data_to_binary() == bytes([0xF7, 0x01])


class TestVeryFastBlinkingLedMessage:
    """Tests for VeryFastBlinkingLedMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = VeryFastBlinkingLedMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]))
        assert msg.leds == [1]
        assert msg.data_to_binary() == bytes([0xF9, 0x01])


class TestUpdateLedStatusMessage:
    """Tests for UpdateLedStatusMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = UpdateLedStatusMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x04]))
        assert msg.led_on == [1]
        assert msg.led_slow_blinking == [2]
        assert msg.led_fast_blinking == [3]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = UpdateLedStatusMessage()
        msg.led_on = [1]
        msg.led_slow_blinking = [2]
        msg.led_fast_blinking = [3]
        assert msg.data_to_binary() == bytes([0xF4, 0x01, 0x02, 0x04])
