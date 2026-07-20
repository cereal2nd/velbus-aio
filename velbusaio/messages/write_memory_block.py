"""Write Memory Block message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage, RawTailField

COMMAND_CODE = 0xCA


@register(COMMAND_CODE)
class WriteMemoryBlockMessage(DeclarativeMessage):
    """Write Memory Block message class."""

    _command_code = COMMAND_CODE
    _data_length = 6

    high_address = ByteField(0)
    low_address = ByteField(1)
    data = RawTailField(2, default=b"")

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.high_address, self.low_address, *self.data])
