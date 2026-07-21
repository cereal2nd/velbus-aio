"""PSU Load Message.

:author: Maikel Punie
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage

COMMAND_CODE = 0xA2
BALANCED = 0x01
BOOST = 0x02
BACKUP = 0x03


@register(COMMAND_CODE)
class PsuLoadMessage(DeclarativeMessage):
    """PSU Load Message."""

    _command_code = COMMAND_CODE
    _data_length = 4

    mode = ByteField(0)
    load_1 = ByteField(1)
    load_2 = ByteField(2)
    out = ByteField(3)
