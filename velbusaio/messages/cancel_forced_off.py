"""Cancel Forced Off message class."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage

COMMAND_CODE = 0x13


@register(COMMAND_CODE)
class CancelForcedOff(DeclarativeMessage):
    """Cancel Forced Off message."""

    _command_code = COMMAND_CODE
    _priority = "high"

    channel = ByteField(0)
