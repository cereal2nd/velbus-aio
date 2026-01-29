"""Update LED Status Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xF4


@register(COMMAND_CODE)
class UpdateLedStatusMessage(Message):
    """Update LED Status Message."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize UpdateLedStatusMessage instance."""
        super().__init__()
        self.led_on = []
        self.led_slow_blinking = []
        self.led_fast_blinking = []
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 3)
        self.set_attributes(priority, address, rtr)
        self.led_on = self.byte_to_channels(data[0])
        self.led_slow_blinking = self.byte_to_channels(data[1])
        self.led_fast_blinking = self.byte_to_channels(data[2])

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte(self.led_on),
                self.channels_to_byte(self.led_slow_blinking),
                self.channels_to_byte(self.led_fast_blinking),
            ]
        )
