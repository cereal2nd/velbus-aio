"""Set Temperature Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ComputedField, DeclarativeMessage, Field

COMMAND_CODE = 0xE4


@register(COMMAND_CODE)
class SetTemperatureMessage(DeclarativeMessage):
    """Set Temperature Message."""

    _command_code = COMMAND_CODE
    _data_length = 1

    temp_type = ComputedField(parser=lambda data: 0, default=0, serializable=True)
    temp = Field(
        byte_index=1,
        default=0,
        parser=lambda data: data[1] * 2,
        serializer=lambda value: bytes([int(value)]),
    )
