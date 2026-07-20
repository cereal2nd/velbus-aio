"""IR Receiver Status message class.

:author: David Danssaert <david.danssaert@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ChannelsField, DeclarativeMessage

COMMAND_CODE = 0xEB


@register(COMMAND_CODE, ["VMB8IR"])
class IRReceiverStatusMessage(DeclarativeMessage):
    """IR Receiver Status message."""

    _command_code = COMMAND_CODE
    _data_length = 4

    closed = ChannelsField(0)
    led_on = ChannelsField(1)
    led_slow_blinking = ChannelsField(2)
    led_fast_blinking = ChannelsField(3)
