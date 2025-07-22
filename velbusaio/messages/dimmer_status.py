"""
:author: Frank van Breugel
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xEE
MODE_START_STOP = 0x00
MODE_STAIRCASE = 0x01
MODE_DIMMER = 0x02
MODE_MEMORY = 0x03
MODE_MULTI = 0x04
MODE_SLOW_ON = 0x05
MODE_SLOW_OFF = 0x06
MODE_SLOW = 0x06
LED_OFF = 0
LED_ON = 1 << 7
LED_SLOW_BLINKING = 1 << 6
LED_FAST_BLINKING = 1 << 5
LED_VERY_FAST_BLINKING = 1 << 4


@register(
    COMMAND_CODE,
    [
        "VMB1DM",
        "VMBDME",
        "VMB1LED",
        "VMBDALI",
        "VMBDALI-20",
        "VMB8DC-20",
        "VMB4LEDPWM-20",
    ],
)
class DimmerStatusMessage(Message):
    """
    sent by: VMBDME
    received by:
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.channel = 1
        self.disable_inhibit_forced = 0
        self.dimmer_mode = 0
        self.dimmer_state = 0
        self.led_status = 0
        self.delay_time = 0
        self.set_defaults(address)
        self.dimmer_config = 0

    def populate(self, priority, address, rtr, data):
        """
        :return: None
        """
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.dimmer_mode = data[0]
        self.channel = 1
        self.dimmer_state = int.from_bytes([data[1]], byteorder="big", signed=False)
        self.led_status = data[2]
        (self.delay_time,) = struct.unpack(">L", bytes([0]) + data[4:])
        self.dimmer_config = data[6]

    def is_start_stop(self):
        """
        :return: bool
        """
        return self.dimmer_mode == MODE_START_STOP

    def is_dimmer(self):
        """
        :return: bool
        """
        return self.dimmer_mode == MODE_DIMMER

    def is_dimmer_memory(self):
        """
        :return: bool
        """
        return self.dimmer_mode == MODE_MEMORY

    def is_staircase(self):
        """
        :return: bool
        """
        return self.dimmer_mode == MODE_STAIRCASE

    def is_multi(self):
        """
        :return: bool
        """
        return self.dimmer_mode == MODE_MULTI

    def is_slow(self):
        """
        :return: bool
        """
        return self.dimmer_mode == MODE_SLOW

    def is_slow_on(self):
        """
        :return: bool
        """
        return self.dimmer_mode == MODE_SLOW_ON

    def is_slow_off(self):
        """
        :return: bool
        """
        return self.dimmer_mode == MODE_SLOW_OFF

    def cur_dimmer_state(self):
        """
        :return: int
        """
        return self.dimmer_state

    def data_to_binary(self):
        """
        :return: bytes
        """
        return (
            bytes(
                [
                    COMMAND_CODE,
                    self.dimmer_mode,
                    self.dimmer_state,
                    self.led_status,
                ]
            )
            + struct.pack(">L", self.delay_time)[-3:]
        )
