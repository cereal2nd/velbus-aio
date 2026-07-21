"""Relay Status Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    ByteField,
    ChannelField,
    DeclarativeMessage,
    Int24Field,
)

COMMAND_CODE = 0xFB
CHANNEL_NORMAL = 0x00
CHANNEL_INHIBITED = 0x01
CHANNEL_FORCED_ON = 0x02
CHANNEL_DISABLED = 0x03
RELAY_ON = 0x01
RELAY_OFF = 0x00
INTERVAL_TIMER_ON = 0x03
LED_OFF = 0
LED_ON = 1 << 7
LED_SLOW_BLINKING = 1 << 6
LED_FAST_BLINKING = 1 << 5
LED_VERY_FAST_BLINKING = 1 << 4


@register(COMMAND_CODE)
class RelayStatusMessage(DeclarativeMessage):
    """Relay Status Message."""

    _command_code = COMMAND_CODE
    _data_length = 7

    channel = ChannelField(0)
    disable_inhibit_forced = ByteField(1)
    status = ByteField(2)
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

    def is_on(self):
        """:return: bool"""
        return self.status == RELAY_ON

    def has_interval_timer_on(self):
        """:return: bool"""
        return self.status == INTERVAL_TIMER_ON


@register(COMMAND_CODE)
class RelayStatusMessage2(RelayStatusMessage):
    """Relay Status Message."""

    def is_on(self):
        """:return: bool"""
        return (self.status >> (self.channel - 1)) & 1 != 0


@register(COMMAND_CODE)
class RelayStatusMessage3(DeclarativeMessage):
    """Relay Status Message."""

    _command_code = COMMAND_CODE
    _data_length = 7
    _generates_data_to_binary = False

    status_bits = ByteField(0)
    inhibited_bits = ByteField(1)
    forced_on_bits = ByteField(2)
    forced_off_bits = ByteField(3)
    program_disabled_bits = ByteField(4)
    interval_timer_bits = ByteField(5)
    alarm_bits = ByteField(6)

    def is_on(self, channel):
        """:return: bool"""
        return (self.status_bits >> (channel - 1)) & 1 != 0

    def is_inhibited(self, channel):
        """:return: bool"""
        return (self.inhibited_bits >> (channel - 1)) & 1 != 0

    def is_forced_on(self, channel):
        """:return: bool"""
        return (self.forced_on_bits >> (channel - 1)) & 1 != 0

    def is_forced_off(self, channel):
        """:return: bool"""
        return (self.forced_off_bits >> (channel - 1)) & 1 != 0

    def is_program_disabled(self, channel):
        """:return: bool"""
        return (self.program_disabled_bits >> (channel - 1)) & 1 != 0

    def has_interval_timer_on(self, channel):
        """:return: bool"""
        return (self.interval_timer_bits >> (channel - 1)) & 1 != 0
