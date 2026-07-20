"""Set Dimmer Message.

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

COMMAND_CODE = 0x07


def _parse_transition(data: bytes) -> int:
    return int.from_bytes(data[2:4], byteorder="big", signed=False)


def _serialize_transition(value: int) -> bytes:
    return value.to_bytes(2, byteorder="big", signed=False)


@register(
    COMMAND_CODE,
    ["VMB1DM", "VMBDME", "VMB4DC", "VMB1LED"],
)
class SetDimmerMessage(DeclarativeMessage):
    """Set Dimmer Message.

    with this message the channel numbering is a bitnumber
    """

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 4

    dimmer_channels = ChannelsField(0)
    dimmer_state = ByteField(1)
    dimmer_transitiontime = Field(
        default=0,
        parser=_parse_transition,
        serializer=_serialize_transition,
    )


@register(
    COMMAND_CODE,
    [
        "VMBDALI",
        "VMBDALI-20",
        "VMBDMI",
        "VMBDMI-R",
        "VMB8DC-20",
        "VMB4LEDPWM-20",
        "VMB2DC-20",
    ],
)
class SetDimmerMessage2(SetDimmerMessage):
    """Set Dimmer Message.

    This with this message the channel numbering is an integer
    """

    dimmer_channels = ChannelIndexField(0)

    def channels_to_byte(self, channels) -> int:
        """Channels to byte."""
        if len(channels) != 1:
            raise ValueError("We should have exact one channel")
        return channels[0]
