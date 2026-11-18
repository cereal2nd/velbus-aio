"""Restore Dimmer Message.

:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_effects import RestoreBrightness, first_channel
from velbusaio.command_registry import register
from velbusaio.message_fields import (
    ByteField,
    ChannelIndexField,
    ChannelsField,
    DeclarativeMessage,
    Int16Field,
)

COMMAND_CODE = 0x11


@register(COMMAND_CODE)
class RestoreDimmerMessage(DeclarativeMessage):
    """Restore Dimmer Message.

    With this message the channel numbering is a bitnumber.
    """

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 4

    dimmer_channels = ChannelsField(0)
    _padding = ByteField(1, default=0)
    dimmer_transitiontime = Int16Field(2)

    def command_effect(self) -> RestoreBrightness | None:
        """Return a :class:`~velbusaio.command_effects.CommandEffect` for Signum translation."""
        channel = first_channel(self.dimmer_channels)
        if channel is None:
            return None
        return RestoreBrightness(channel=channel)


@register(COMMAND_CODE)
class RestoreDimmerMessage2(RestoreDimmerMessage):
    """Restore Dimmer Message.

    With this message the channel numbering is an integer.
    """

    dimmer_channels = ChannelIndexField(0)
    # VMB2DC-20 / VMB4LEDPWM-20 use the SetDimmer frame layout; 0xFF = restore
    # last active level (see openhab VelbusSetDimPacket.setLastUsedDim).
    _padding = ByteField(1, default=255)
