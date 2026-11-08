"""TempSensorSettingsPart4 message implementation.

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

COMMAND_CODE = 0xB9


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


def _optional_half(index: int, default: float = 0.0) -> HalfDegreeField:
    return HalfDegreeField(index, default=default)


@register(COMMAND_CODE)
class TempSensorSettingsPart4(DeclarativeMessage):
    """Fourth part of temperature sensor settings.

    Classic VMB1TS only carries minimum switching time. Glass-panel modules
    add pump delays, extra alarms and heat/cool range limits.
    """

    _command_code = COMMAND_CODE
    _data_length = 1
    _generates_data_to_binary = False

    min_switching_time = ByteField(0, default=0)
    pump_delayed_on = _optional_byte(1, 0)
    pump_delayed_off = _optional_byte(2, 0)
    alarm_2 = _optional_half(3)
    alarm_3 = _optional_half(4)
    heat_lower = _optional_half(5)
    cool_upper = _optional_half(6)

    def __init__(self, address: int | None = None, *, layout: str = "gp") -> None:
        """Initialize with a settings layout (``classic`` or ``gp``)."""
        Message.__init__(self)
        for field_name, field_desc in self._declarative_fields.items():
            setattr(self, field_name, field_desc.default)
        self.set_defaults(address)
        self.layout = layout

    def data_to_binary(self) -> bytes:
        """Serialize, truncating GP-only bytes for classic layout."""
        result = bytes([COMMAND_CODE])
        result += self._declarative_fields["min_switching_time"].serialize(
            self.min_switching_time
        )
        if self.layout == "classic":
            return result
        for name in (
            "pump_delayed_on",
            "pump_delayed_off",
            "alarm_2",
            "alarm_3",
            "heat_lower",
            "cool_upper",
        ):
            field = self._declarative_fields[name]
            result += field.serialize(getattr(self, name))
        return result
