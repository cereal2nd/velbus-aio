"""Restore Dimmer Message.

:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import Message

COMMAND_CODE = 0x11


@register(
    COMMAND_CODE,
    [
        "VMB1DM",
        "VMBDME",
        "VMBDMI-R",
        "VMBDMI",
        "VMB1LED",
        "VMB4DC",
        "VMB8DC-20",
        "VMB2DC-20",
        "VMB4LEDPWM-20",
    ],
)
class RestoreDimmerMessage(Message):
    """Restore Dimmer Message."""

    command_code = COMMAND_CODE
    default_priority = PRIORITY_HIGH

    def __init__(self, address=None):
        """Initialize Restore Dimmer Message Object."""
        super().__init__()
        self.dimmer_channels = []
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        self.dimmer_channels = self.byte_to_channels(data[0])
        self.dimmer_transitiontime = int.from_bytes(
            data[2:3], byteorder="big", signed=False
        )

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte(self.dimmer_channels),
                0,
            ]
        ) + self.dimmer_transitiontime.to_bytes(2, byteorder="big", signed=False)


@register(COMMAND_CODE, ["VMBDALI", "VMBDALI-20"])
class RestoreDimmerMessage2(RestoreDimmerMessage):
    """Restore Dimmer Message."""

    def byte_to_channels(self, byte: int) -> list[int]:
        """Break down byte into list of channels."""
        return [byte]

    def channels_to_byte(self, channels: list[int]) -> int:
        """Convert list of channels into byte."""
        if len(channels) != 1:
            raise ValueError("We should have exact one channel")
        return channels[0]
