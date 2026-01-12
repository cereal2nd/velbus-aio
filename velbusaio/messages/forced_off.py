"""Forced Off message class."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import Message

COMMAND_CODE = 0x12


@register(COMMAND_CODE)
class ForcedOff(Message):
    """Forced Off message."""

    def __init__(self, address=None):
        """Iniatialize Forced Off message object."""
        Message.__init__(self, address)
        self.priority = PRIORITY_HIGH
        self.channel = 0
        self.delay_time = 0

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)
        self.channel = data[0]
        self.delay_time = (data[1] << 16) + (data[2] << 8) + data[3]

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.channel,
                (self.delay_time >> 16) & 0xFF,
                (self.delay_time >> 8) & 0xFF,
                self.delay_time & 0xFF,
            ]
        )
