"""Set Temperature Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ComputedField, DeclarativeMessage, Field

COMMAND_CODE = 0xE4


def _parse_temp(data: bytes) -> float:
    raw = data[1]
    if raw & 0x80:
        raw -= 0x100
    return raw / 2


def _serialize_temp(value: float) -> bytes:
    return bytes([int(round(value * 2)) & 0xFF])


@register(COMMAND_CODE)
class SetTemperatureMessage(DeclarativeMessage):
    """Set Temperature Message.

    The temperature is expressed in degrees Celsius. On the wire DATABYTE3
    holds the value in two's complement with a resolution of 0.5 degrees.
    """

    _command_code = COMMAND_CODE
    _data_length = 2

    temp_type = ComputedField(parser=lambda data: 0, default=0, serializable=True)
    temp = Field(
        byte_index=1,
        default=0,
        parser=_parse_temp,
        serializer=_serialize_temp,
    )
