"""
:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xF1


@register(COMMAND_CODE)
class ChannelNamePart2Message(Message):
    """
    send by: VMB6IN, VMB4RYLD
    received by:
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.channel = 0
        self.name = ""
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """
        :return: None
        """
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        channels = self.byte_to_channels(data[0])
        self.needs_one_channel(channels)
        self.channel = channels[0]
        self.name = "".join([chr(x) for x in data[1:]])

    def data_to_binary(self):
        """
        :return: bytes
        """
        return bytes([COMMAND_CODE, self.channels_to_byte([self.channel])]) + bytes(
            self.name, "ascii", "ignore"
        )


@register(
    COMMAND_CODE,
    [
        "VMBGP1",
        "VMBEL1",
        "VMBGP1-2",
        "VMBGP2",
        "VMBEL2",
        "VMBGP2-2",
        "VMBGP4",
        "VMBEL4",
        "VMBGP4-2",
        "VMBGPO",
        "VMBGPOD",
        "VMBGPOD-2",
        "VMBELO",
        "VMBGP4PIR",
        "VMBGP4PIR-2",
        "VMBDMI",
        "VMBDMI-R",
        "VMBIN",
        "VMBKP",
        "VMBELPIR",
        "VMBDALI",
        "VMB4AN",
        "VMB6PB-20",
        "VMBEL1-20",
        "VMBEL2-20",
        "VMBEL4-20",
        "VMBELO-20",
        "VMBGP1-20",
        "VMBGP2-20",
        "VMBGP4-20",
        "VMBGPO-20",
        "VMBDALI-20",
        "VMBEL4PIR-20",
        "VMBGP4PIR-20",
        "VMB8DC-20",
        "VMB2DC-20",
        "VMB8IN-20",
        "VMB4LEDPWM-20",
        "VMBPSUMNGR-20",
    ],
)
class ChannelNamePart2Message2(ChannelNamePart2Message):
    """
    send by: VMBGP*, VMBDALI
    received by:
    """

    def populate(self, priority, address, rtr, data):
        """
        :return: None
        """
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.channel = data[0]
        self.name = "".join([chr(x) for x in data[1:]])


@register(COMMAND_CODE, ["VMB1BL", "VMB2BL"])
class ChannelNamePart2Message3(ChannelNamePart2Message):
    """
    send by: VMBGP*
    received by:
    """

    def populate(self, priority, address, rtr, data):
        """
        :return: None
        """
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 5)
        self.set_attributes(priority, address, rtr)
        self.channel = (data[0] >> 1) & 0x03
        self.name = "".join([chr(x) for x in data[1:]])
