"""Memo Text Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xAC


@register(COMMAND_CODE)
class MemoTextMessage(DeclarativeMessage):
    """Memo Text Message."""

    _command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize Memo Text Message object."""
        super().__init__(address)
        self.start = 0x00
        self.memo_text = ""

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)
        self.start = data[1]
        self.name = "".join(chr(x) for x in data[2:])

    def data_to_binary(self):
        """:return: bytes"""
        memo_text = self.memo_text
        while len(memo_text) < 5:
            memo_text += chr(0)
        return bytes([COMMAND_CODE, 0x00, self.start]) + bytes(memo_text, "utf-8")
