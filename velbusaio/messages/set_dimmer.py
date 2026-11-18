"""Set Dimmer Message.

:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_effects import SetBrightness, first_channel
from velbusaio.command_registry import register
from velbusaio.message_fields import (
    ByteField,
    ChannelIndexField,
    ChannelsField,
    DeclarativeMessage,
    Int16Field,
)

COMMAND_CODE = 0x07


@register(COMMAND_CODE)
class SetDimmerMessage(DeclarativeMessage):
    """Set Dimmer Message.

    with this message the channel numbering is a bitnumber
    """

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 4

    dimmer_channels = ChannelsField(0)
    dimmer_state = ByteField(1)
    dimmer_transitiontime = Int16Field(2)

    def command_effect(self) -> SetBrightness | None:
        """Return a :class:`~velbusaio.command_effects.CommandEffect` for Signum translation."""
        channel = first_channel(self.dimmer_channels)
        if channel is None:
            return None
        transition = (
            int(self.dimmer_transitiontime) if self.dimmer_transitiontime else None
        )
        return SetBrightness(
            channel=channel,
            level=int(self.dimmer_state),
            transition_time=transition,
        )


@register(COMMAND_CODE)
class SetDimmerMessage2(SetDimmerMessage):
    """Set Dimmer Message.

    This with this message the channel numbering is an integer
    """

    dimmer_channels = ChannelIndexField(0)

    def channels_to_byte(self, channels: list[int]) -> int:
        """Channels to byte."""
        if len(channels) != 1:
            raise ValueError("We should have exact one channel")
        return int(channels[0])
