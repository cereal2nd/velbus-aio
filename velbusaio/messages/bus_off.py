"""Bus Off message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0x09


@register(COMMAND_CODE)
class BusOffMessage(DeclarativeMessage):
    """Bus Off message."""

    _command_code = COMMAND_CODE
    _data_length = 0
