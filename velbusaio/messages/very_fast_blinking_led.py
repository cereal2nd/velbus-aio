"""Very Fast Blinking LED message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ChannelsField, DeclarativeMessage

COMMAND_CODE = 0xF9


@register(COMMAND_CODE)
class VeryFastBlinkingLedMessage(DeclarativeMessage):
    """Very Fast Blinking LED message."""

    _command_code = COMMAND_CODE
    _data_length = 1

    leds = ChannelsField(0)
