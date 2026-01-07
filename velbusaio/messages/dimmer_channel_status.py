"""Dimmer Channel Status message class.

:author: Frank van Breugel
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message import Message

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


@register(
    COMMAND_CODE,
    ["VMB4DC", "VMBDMI", "VMBDMI-R", "VMB8DC-20", "VMB4LEDPWM-20", "VMB2DC-20"],
)
class DimmerChannelStatusMessage(Message):
    """Dimmer Channel Status message."""

    def __init__(self, address=None):
        """Initialize Dimmer Channel Status message."""
        Message.__init__(self)
        self.channel = 1
        self.disable_inhibit_forced = 0
        self.dimmer_state = 0
        self.led_status = 0
        self.delay_time = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.channel = self.byte_to_channel(data[0])
        self.disable_inhibit_forced = data[1]
        self.dimmer_state = int.from_bytes([data[2]], byteorder="big", signed=False)
        self.led_status = data[3]
        (self.delay_time,) = struct.unpack(">L", bytes([0]) + data[4:])

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

    def data_to_binary(self):
        """:return: bytes"""
        return (
            bytes(
                [
                    COMMAND_CODE,
                    self.channels_to_byte([self.channel]),
                    self.disable_inhibit_forced,
                    self.dimmer_state,
                    self.led_status,
                ]
            )
            + struct.pack(">L", self.delay_time)[-3:]
        )
