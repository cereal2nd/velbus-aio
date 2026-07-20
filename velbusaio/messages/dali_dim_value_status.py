"""Dali Dim Value Status message class.

:author: Niels Laukens
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage, Field

COMMAND_CODE = 0xA5


@register(
    COMMAND_CODE, ["VMBDALI", "VMBDALI-20", "VMB8DC-20", "VMB4LEDPWM-20", "VMB2DC-20"]
)
class DimValueStatus(DeclarativeMessage):
    """Dali Dim Value Status message."""

    _command_code = COMMAND_CODE
    _data_length = 2

    channel = ByteField(0, default=0)
    dim_values = Field(
        default=[],
        parser=lambda data: list(data[1:]),
        serializer=bytes,
    )
