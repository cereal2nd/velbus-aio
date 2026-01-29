"""Set Dimmer Message.

:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import Message

COMMAND_CODE = 0x07


@register(
    COMMAND_CODE,
    ["VMB1DM", "VMBDME", "VMB4DC", "VMB1LED"],
)
class SetDimmerMessage(Message):
    """Set Dimmer Message.

    with this message the channel numbering is a bitnumber
    """

    command_code = COMMAND_CODE
    default_priority = PRIORITY_HIGH

    def __init__(self, address=None):
        """Initialize Set Dimmer Message Object."""
        super().__init__()
        self.dimmer_channels = []
        self.dimmer_state = 0
        self.dimmer_transitiontime = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 4)
        self.set_attributes(priority, address, rtr)
        self.dimmer_channels = self.byte_to_channels(data[0])
        self.dimmer_state = data[1]
        self.dimmer_transitiontime = int.from_bytes(
            data[2:3], byteorder="big", signed=False
        )

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte(self.dimmer_channels),
                self.dimmer_state,
            ]
        ) + self.dimmer_transitiontime.to_bytes(2, byteorder="big", signed=False)


@register(
    COMMAND_CODE,
    [
        "VMBDALI",
        "VMBDALI-20",
        "VMBDMI",
        "VMBDMI-R",
        "VMB8DC-20",
        "VMB4LEDPWM-20",
        "VMB2DC-20",
    ],
)
class SetDimmerMessage2(SetDimmerMessage):
    """Set Dimmer Message.

    This with this message the channel numbering is an integer
    """

    def byte_to_channels(self, byte: int) -> list[int]:
        """Byte to channels."""
        return [byte]

    def channels_to_byte(self, channels) -> int:
        """Channels to byte."""
        if len(channels) != 1:
            raise ValueError("We should have exact one channel")
        return channels[0]
