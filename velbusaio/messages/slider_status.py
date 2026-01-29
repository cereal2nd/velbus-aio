"""Slider Status Message.

:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0x0F


@register(
    COMMAND_CODE,
    [
        "VMB1DM",
        "VMBDME",
        "VMB4DC",
        "VMBDMI",
        "VMBDMI-R",
        "VMB1LED",
        "VMB8DC-20",
        "VMB2DC-20",
        "VMB4LEDPWM-20",
    ],
)
class SliderStatusMessage(Message):
    """Slider Status Message."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize Slider Status Message Object."""
        super().__init__()
        self.channel = 0
        self.slider_state = 0
        self.slider_long_pressed = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 3)
        self.set_attributes(priority, address, rtr)
        self.channel = self.byte_to_channel(data[0])
        self.slider_state = int.from_bytes([data[1]], byteorder="big")
        self.slider_long_pressed = data[2]

    def cur_slider_state(self):
        """:return: int"""
        return self.slider_state

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte([self.channel]),
                self.slider_state,
                self.slider_long_pressed,
            ]
        )
