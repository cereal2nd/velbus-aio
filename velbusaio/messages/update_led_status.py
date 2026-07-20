"""Update LED Status Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ChannelsField, DeclarativeMessage

COMMAND_CODE = 0xF4


@register(COMMAND_CODE)
class UpdateLedStatusMessage(DeclarativeMessage):
    """Update LED Status Message."""

    _command_code = COMMAND_CODE
    _data_length = 3

    led_on = ChannelsField(0)
    led_slow_blinking = ChannelsField(1)
    led_fast_blinking = ChannelsField(2)
