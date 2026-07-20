"""Read Data Block From Memory Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage

COMMAND_CODE = 0xFD


@register(COMMAND_CODE)
class ReadDataFromMemoryMessage(DeclarativeMessage):
    """Read Data From Memory Message."""

    _command_code = COMMAND_CODE
    _data_length = 2

    high_address = ByteField(0)
    low_address = ByteField(1)
