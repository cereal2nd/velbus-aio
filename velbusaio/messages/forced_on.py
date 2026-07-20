"""Forced On message class."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage, Field

COMMAND_CODE = 0x14


@register(COMMAND_CODE)
class ForcedOn(DeclarativeMessage):
    """Forced On message."""

    _command_code = COMMAND_CODE
    _priority = "high"

    channel = ByteField(0)
    delay_time = Field(
        byte_index=1,
        default=0,
        parser=lambda data: (data[1] << 16) + (data[2] << 8) + data[3],
        serializer=lambda value: bytes(
            [(value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF]
        ),
    )
