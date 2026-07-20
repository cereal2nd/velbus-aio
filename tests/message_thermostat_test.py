"""Unit tests for the thermostat mode-switch message classes."""

from __future__ import annotations

import pytest

from velbusaio.const import PRIORITY_LOW
from velbusaio.messages.switch_to_comfort import SwitchToComfortMessage
from velbusaio.messages.switch_to_day import SwitchToDayMessage
from velbusaio.messages.switch_to_night import SwitchToNightMessage
from velbusaio.messages.switch_to_safe import SwitchToSafeMessage


@pytest.mark.parametrize(
    ("cls", "code"),
    [
        (SwitchToComfortMessage, 0xDB),
        (SwitchToDayMessage, 0xDC),
        (SwitchToNightMessage, 0xDD),
        (SwitchToSafeMessage, 0xDE),
    ],
)
class TestSwitchToModeMessages:
    """Shared tests for the switch-to-<mode> messages."""

    def test_data_to_binary_no_sleep(self, cls, code):
        """Test Data to binary no sleep."""
        assert cls().data_to_binary() == bytes([code, 0x00, 0x00])

    def test_data_to_binary_with_sleep(self, cls, code):
        """Test Data to binary with sleep."""
        msg = cls(sleep=0x0102)
        assert msg.data_to_binary() == bytes([code, 0x01, 0x02])

    def test_populate_sets_attributes(self, cls, code):
        """Test Populate sets attributes."""
        msg = cls()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([]))
        assert msg.address == 0x01
        assert msg.rtr is False
