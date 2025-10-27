"""
:author: Frank van Breugel
"""

from __future__ import annotations

from velbusaio.command_registry import register
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
    """
    send by:
    received by: VMBDME, VMB4DC
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.dimmer_channels = []
        self.set_defaults(address)

    def set_defaults(self, address):
        if address is not None:
            self.set_address(address)
        self.set_high_priority()
        self.set_no_rtr()

    def populate(self, priority, address, rtr, data):
        """
        :return: None
        """
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        self.dimmer_channels = self.byte_to_channels(data[0])
        self.dimmer_transitiontime = int.from_bytes(
            data[2:3], byteorder="big", signed=False
        )

    def data_to_binary(self):
        """
        :return: bytes
        """
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte(self.dimmer_channels),
                0,
            ]
        ) + self.dimmer_transitiontime.to_bytes(2, byteorder="big", signed=False)


@register(COMMAND_CODE, ["VMBDALI", "VMBDALI-20"])
class RestoreDimmerMessage2(RestoreDimmerMessage):
    def byte_to_channels(self, byte: int) -> list[int]:
        return [byte]

    def channels_to_byte(self, channels: list[int]) -> int:
        if len(channels) != 1:
            raise ValueError("We should have exact one channel")
        return channels[0]
