"""Push Button Status Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import Message

COMMAND_CODE = 0x00


@register(COMMAND_CODE)
class PushButtonStatusMessage(Message):
    """Push Button Status Message."""

    command_code = COMMAND_CODE
    default_priority = PRIORITY_HIGH

    def __init__(self, address=None):
        """Initialize Push Button Status Message Object."""
        super().__init__()
        self.closed = []
        self.opened = []
        self.closed_long = []
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 3)
        self.set_attributes(priority, address, rtr)
        self.closed = self.byte_to_channels(data[0])
        self.opened = self.byte_to_channels(data[1])
        self.closed_long = self.byte_to_channels(data[2])

    def set_defaults(self, address):
        """:return: None"""
        if address is not None:
            self.set_address(address)
        self.set_high_priority()
        self.set_no_rtr()

    def get_channels(self):
        """:return: list"""
        return self.closed + self.opened

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte(self.closed),
                self.channels_to_byte(self.opened),
                self.channels_to_byte(self.closed_long),
            ]
        )
