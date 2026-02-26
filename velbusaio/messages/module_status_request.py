"""Module Status Request Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xFA


@register(COMMAND_CODE)
class ModuleStatusRequestMessage(Message):
    """Module Status Request Message."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize Module Status Request Message object."""
        super().__init__()
        self.channels: list | str = []
        self.wait_after_send = 500
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        self.channels = self.byte_to_channels(data[0])

    def data_to_binary(self):
        """:return: bytes"""
        if isinstance(self.channels, list):
            return bytes([COMMAND_CODE, self.channels_to_byte(self.channels)])
        return bytes([COMMAND_CODE, int(self.channels, 16)])
