"""Dimmer Status message class.

:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage, Int24Field

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
class DimmerStatusMessage(DeclarativeMessage):
    """Dimmer Status message."""

    _command_code = COMMAND_CODE
    _data_length = 7

    dimmer_mode = ByteField(0)
    dimmer_state = ByteField(1)
    led_status = ByteField(2)
    delay_time = Int24Field(3)
    dimmer_config = ByteField(6, serializable=False)

    def __init__(self, address=None):
        """Initialize Dimmer Status message."""
        super().__init__(address)
        self.channel = 1

    def _post_populate(self, data: bytes) -> None:
        self.channel = 1

    def is_start_stop(self):
        """:return: bool"""
        return self.dimmer_mode == MODE_START_STOP

    def is_dimmer(self):
        """:return: bool"""
        return self.dimmer_mode == MODE_DIMMER

    def is_dimmer_memory(self):
        """:return: bool"""
        return self.dimmer_mode == MODE_MEMORY

    def is_staircase(self):
        """:return: bool"""
        return self.dimmer_mode == MODE_STAIRCASE

    def is_multi(self):
        """:return: bool"""
        return self.dimmer_mode == MODE_MULTI

    def is_slow(self):
        """:return: bool"""
        return self.dimmer_mode == MODE_SLOW

    def is_slow_on(self):
        """:return: bool"""
        return self.dimmer_mode == MODE_SLOW_ON

    def is_slow_off(self):
        """:return: bool"""
        return self.dimmer_mode == MODE_SLOW_OFF

    def cur_dimmer_state(self):
        """:return: int"""
        return self.dimmer_state

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.dimmer_mode,
                self.dimmer_state,
                self.led_status,
            ]
        ) + Int24Field(3).serialize(self.delay_time)
