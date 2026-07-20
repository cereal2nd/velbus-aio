"""Receive Buffer Full Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0x0B


@register(COMMAND_CODE)
class ReceiveBufferFullMessage(DeclarativeMessage):
    """Receive Buffer Full Message."""

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 0
