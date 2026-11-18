"""Cover Off message.

:author: Tom Dupré <gitd8400@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_effects import CoverMove
from velbusaio.command_registry import register
from velbusaio.message_fields import BlindChannelField, ChannelField, DeclarativeMessage

COMMAND_CODE = 0x04


@register(COMMAND_CODE)
class CoverOffMessage(DeclarativeMessage):
    """Cover Off message."""

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 1

    channel = ChannelField(0, default=0)

    def command_effect(self) -> CoverMove | None:
        """Return a :class:`~velbusaio.command_effects.CommandEffect` for Signum translation."""
        return CoverMove(channel=int(self.channel), motion="stop")


@register(COMMAND_CODE)
class CoverOffMessage2(CoverOffMessage):
    """Cover Off message."""

    channel = BlindChannelField(0, default=0)
