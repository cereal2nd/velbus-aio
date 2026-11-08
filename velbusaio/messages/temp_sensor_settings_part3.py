"""TempSensorSettingsPart3 message implementation.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from collections.abc import Callable

from velbusaio.command_registry import register
from velbusaio.message import Message
from velbusaio.message_fields import (
    ByteField,
    DeclarativeMessage,
    Field,
    HalfDegreeField,
)

COMMAND_CODE = 0xC6


def _parse_optional_byte(data: bytes, index: int, default: int) -> int:
    return data[index] if len(data) > index else default


def _serialize_optional_byte(value: int) -> bytes:
    return bytes([value & 0xFF])


def _make_optional_byte_parser(index: int, default: int) -> Callable[[bytes], int]:
    def parser(data: bytes) -> int:
        return _parse_optional_byte(data, index, default)

    return parser


def _optional_byte(index: int, default: int = 0) -> Field:
    return Field(
        byte_index=index,
        default=default,
        parser=_make_optional_byte_parser(index, default),
        serializer=_serialize_optional_byte,
    )


@register(COMMAND_CODE)
class TempSensorSettingsPart3(DeclarativeMessage):
    """Third part of temperature sensor settings (alarms / ranges / calibration).

    Classic modules (VMB1TS/VMB1TC) use bytes 0/1 as low/high alarms and byte 5
    as differential slave address (6 payload bytes). Glass-panel modules use
    alarm 1/4, zone number and an optional calibration gain byte.
    """

    _command_code = COMMAND_CODE
    _data_length = 6
    _generates_data_to_binary = False

    alarm_low = HalfDegreeField(0)
    alarm_high = HalfDegreeField(1)
    cool_lower = HalfDegreeField(2)
    heat_upper = HalfDegreeField(3)
    calibration = HalfDegreeField(4)
    # Classic: slave address; GP: zone number.
    slave_or_zone = ByteField(5, default=0xFF)
    # GP only; ignored on classic modules that omit this byte.
    calibration_gain = _optional_byte(6, 0)

    def __init__(self, address: int | None = None, *, layout: str = "gp") -> None:
        """Initialize with a settings layout (``classic`` or ``gp``)."""
        Message.__init__(self)
        for field_name, field_desc in self._declarative_fields.items():
            setattr(self, field_name, field_desc.default)
        self.set_defaults(address)
        self.layout = layout

    def data_to_binary(self) -> bytes:
        """Serialize, truncating optional GP byte for classic layout."""
        result = bytes([COMMAND_CODE])
        for name in (
            "alarm_low",
            "alarm_high",
            "cool_lower",
            "heat_upper",
            "calibration",
            "slave_or_zone",
        ):
            field = self._declarative_fields[name]
            result += field.serialize(getattr(self, name))
        if self.layout != "classic":
            result += self._declarative_fields["calibration_gain"].serialize(
                self.calibration_gain
            )
        return result
