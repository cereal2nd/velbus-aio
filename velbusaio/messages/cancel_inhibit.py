"""Cancel Inhibit message class."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import Message

COMMAND_CODE = 0x17


@register(COMMAND_CODE)
class CancelInhibit(Message):
    """Cancel Inhibit message."""

    def __init__(self, address=None):
        """Iniatialize Cancel Inhibit message object."""
        Message.__init__(self, address)
        self.priority = PRIORITY_HIGH
        self.channel = 0

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)
        self.channel = data[0]

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.channel])
