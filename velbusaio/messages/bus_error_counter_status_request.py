"""Bus Error Counter Status Request message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xD9


@register(COMMAND_CODE)
class BusErrorStatusRequestMessage(DeclarativeMessage):
    """Bus Error Counter Status Request message."""

    _command_code = COMMAND_CODE
    _data_length = 0
