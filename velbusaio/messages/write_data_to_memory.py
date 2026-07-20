"""Write Data To Memory message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage

COMMAND_CODE = 0xFC


@register(COMMAND_CODE)
class WriteDataToMemoryMessage(DeclarativeMessage):
    """Write Data To Memory message class."""

    _command_code = COMMAND_CODE
    _data_length = 3

    high_address = ByteField(0)
    low_address = ByteField(1)
    data = ByteField(2)
