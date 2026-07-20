"""Restore Dimmer Message.

:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    ByteField,
    ChannelIndexField,
    ChannelsField,
    DeclarativeMessage,
    Field,
)

COMMAND_CODE = 0x11


def _parse_transition(data: bytes) -> int:
    return int.from_bytes(data[2:4], byteorder="big", signed=False)


def _serialize_transition(value: int) -> bytes:
    return value.to_bytes(2, byteorder="big", signed=False)


@register(
    COMMAND_CODE,
    [
        "VMB1DM",
        "VMBDME",
        "VMBDMI-R",
        "VMBDMI",
        "VMB1LED",
        "VMB4DC",
        "VMB8DC-20",
        "VMB2DC-20",
        "VMB4LEDPWM-20",
    ],
)
class RestoreDimmerMessage(DeclarativeMessage):
    """Restore Dimmer Message."""

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 4

    dimmer_channels = ChannelsField(0)
    _padding = ByteField(1, default=0)
    dimmer_transitiontime = Field(
        default=0,
        parser=_parse_transition,
        serializer=_serialize_transition,
    )


@register(COMMAND_CODE, ["VMBDALI", "VMBDALI-20"])
class RestoreDimmerMessage2(RestoreDimmerMessage):
    """Restore Dimmer Message."""

    dimmer_channels = ChannelIndexField(0)
