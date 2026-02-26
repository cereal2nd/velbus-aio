"""Start relay blinking timer message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import Message

COMMAND_CODE = 0x0D


@register(COMMAND_CODE)
class StartRelayBlinkingTimerMessage(Message):
    """Start relay blinking timer message."""

    command_code = COMMAND_CODE
    default_priority = PRIORITY_HIGH

    def __init__(self, address=None):
        """Set up a new StartRelayBlinkingTimerMessage instance."""
        super().__init__()
        self.relay_channels = []
        self.delay_time = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 4)
        self.set_attributes(priority, address, rtr)
        self.relay_channels = self.byte_to_channels(data)
        (self.delay_time,) = struct.unpack(">L", bytes([0]) + data[1:])

    def data_to_binary(self):
        """:return: bytes"""
        return (
            bytes([COMMAND_CODE, self.channels_to_byte(self.relay_channels)])
            + struct.pack(">L", self.delay_time)[-3:]
        )
