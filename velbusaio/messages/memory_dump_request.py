"""Memory Dump Request Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xCB


@register(COMMAND_CODE)
class MemoryDumpRequestMessage(DeclarativeMessage):
    """Memory Dump Request Message."""

    _command_code = COMMAND_CODE
    _data_length = 0
