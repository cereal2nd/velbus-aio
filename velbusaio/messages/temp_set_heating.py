"""Temp Set Heating Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xE0


@register(COMMAND_CODE)
class TempSetHeatingMessage(Message):
    """Set Heating Temperature Message."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize TempSetHeatingMessage class."""
        super().__init__()
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, 0xAA])
