"""Switch to day message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xDC


@register(COMMAND_CODE)
class SwitchToDayMessage(Message):
    """Switch to day message class."""

    def __init__(self, address=None, sleep=0):
        """Initialize SwitchToDayMessage instance."""
        Message.__init__(self)
        self.sleep = sleep
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.sleep >> 8, self.sleep & 0xFF])
