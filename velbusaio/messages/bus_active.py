"""Bus Active message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0x0A


@register(COMMAND_CODE)
class BusActiveMessage(DeclarativeMessage):
    """Bus Active message."""

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 0
