"""Counter Status Request message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xBD


@register(COMMAND_CODE, ["VMB7IN", "VMB8IN-20"])
class CounterStatusRequestMessage(Message):
    """Counter Status Request message."""

    def __init__(self, address=None):
        """Initialize Counter Status Request message."""
        Message.__init__(self)
        self.channels = []
        self.wait_after_send = 500
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 2)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.channels_to_byte(self.channels), 0x00])
