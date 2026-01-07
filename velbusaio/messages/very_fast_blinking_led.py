"""Very Fast Blinking LED message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xF9


@register(COMMAND_CODE)
class VeryFastBlinkingLedMessage(Message):
    """Very Fast Blinking LED message class."""

    def __init__(self, address=None):
        """Initialize VeryFastBlinkingLedMessage instance."""
        Message.__init__(self)
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
