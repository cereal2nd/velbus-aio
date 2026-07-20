"""Reads memory data block from Velbus module.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage, RawTailField

COMMAND_CODE = 0xCC


@register(COMMAND_CODE)
class MemoryDataBlockMessage(DeclarativeMessage):
    """Memory Data Block Message."""

    _command_code = COMMAND_CODE
    _data_length = 6

    high_address = ByteField(0)
    low_address = ByteField(1)
    data = RawTailField(2, default=b"")
