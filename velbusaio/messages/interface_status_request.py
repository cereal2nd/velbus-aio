"""Interface Status Request message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0x0E


@register(COMMAND_CODE)
class InterfaceStatusRequestMessage(DeclarativeMessage):
    """Interface Status Request message."""

    _command_code = COMMAND_CODE
    _data_length = 0
