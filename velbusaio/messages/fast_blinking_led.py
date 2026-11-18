"""Fast Blinking LED message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_effects import SetLed, led_command_effect
from velbusaio.command_registry import register
from velbusaio.message_fields import ChannelsField, DeclarativeMessage

COMMAND_CODE = 0xF8


@register(COMMAND_CODE)
class FastBlinkingLedMessage(DeclarativeMessage):
    """Fast Blinking LED message."""

    _command_code = COMMAND_CODE
    _data_length = 1

    leds = ChannelsField(0)

    def command_effect(self) -> SetLed | None:
        """Return a :class:`~velbusaio.command_effects.CommandEffect` for Signum translation."""
        return led_command_effect(self.leds, "fast")
