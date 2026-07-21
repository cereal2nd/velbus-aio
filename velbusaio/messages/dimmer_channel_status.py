"""Dimmer Channel Status message class.

:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    ByteField,
    ChannelField,
    DeclarativeMessage,
    Int24Field,
)

COMMAND_CODE = 0xB8
CHANNEL_NORMAL = 0x00
CHANNEL_INHIBITED = 0x01
CHANNEL_FORCED_ON = 0x02
CHANNEL_DISABLED = 0x03

LED_OFF = 0
LED_ON = 1 << 7
LED_SLOW_BLINKING = 1 << 6
LED_FAST_BLINKING = 1 << 5
LED_VERY_FAST_BLINKING = 1 << 4


@register(COMMAND_CODE)
class DimmerChannelStatusMessage(DeclarativeMessage):
    """Dimmer Channel Status message."""

    _command_code = COMMAND_CODE
    _data_length = 7

    channel = ChannelField(0, default=1)
    disable_inhibit_forced = ByteField(1)
    dimmer_state = ByteField(2)
    led_status = ByteField(3)
    delay_time = Int24Field(4)

    def is_normal(self):
        """:return: bool"""
        return self.disable_inhibit_forced == CHANNEL_NORMAL

    def is_inhibited(self):
        """:return: bool"""
        return self.disable_inhibit_forced == CHANNEL_INHIBITED

    def is_forced_on(self):
        """:return: bool"""
        return self.disable_inhibit_forced == CHANNEL_FORCED_ON

    def is_disabled(self):
        """:return: bool"""
        return self.disable_inhibit_forced == CHANNEL_DISABLED

    def cur_dimmer_state(self):
        """:return: int"""
        return self.dimmer_state
