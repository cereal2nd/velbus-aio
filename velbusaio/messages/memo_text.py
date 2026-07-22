"""Memo Text Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage, Field, StringField

COMMAND_CODE = 0xAC


@register(COMMAND_CODE)
class MemoTextMessage(DeclarativeMessage):
    """Memo Text Message."""

    _command_code = COMMAND_CODE

    start = ByteField(1)
    name = StringField(2)
    memo_text = Field(default="", serializable=False)

    def data_to_binary(self):
        """:return: bytes"""
        memo_text = self.memo_text
        while len(memo_text) < 5:
            memo_text += chr(0)
        return bytes([COMMAND_CODE, 0x00, self.start]) + bytes(memo_text, "utf-8")
