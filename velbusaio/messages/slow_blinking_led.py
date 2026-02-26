"""Set Slow Blinking LED Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xF7


@register(COMMAND_CODE)
class SlowBlinkingLedMessage(Message):
    """Set Slow Blinking LED Message."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize Set Slow Blinking LED Message Object."""
        super().__init__()
        self.leds = []
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        self.leds = self.byte_to_channels(data[0])

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.channels_to_byte(self.leds)])
