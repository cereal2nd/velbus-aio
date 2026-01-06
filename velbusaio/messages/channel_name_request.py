"""Channel Name Request message.

:author: Thomas Delaet <thomas@delaet.org> and Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xEF


@register(COMMAND_CODE)
class ChannelNameRequestMessage(Message):
    """Channel Name Request message."""

    def __init__(self, address=None):
        """Initialize Channel Name Request message."""
        Message.__init__(self)
        self.channels = []
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        self.channels = self.byte_to_channels(data[0])

    def data_to_binary(self):
        """:return: bytes"""
        if isinstance(self.channels, list):
            return bytes([0xEF, self.channels_to_byte(self.channels)])
        return bytes([0xEF, 0xFF])


@register(COMMAND_CODE, ["VMB2BL"])
class ChannelNameRequestMessage2(ChannelNameRequestMessage):
    """Channel Name Request message."""

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        tmp = (data[0] >> 1) & 0x03
        self.channels = self.byte_to_channels(tmp)

    def data_to_binary(self):
        """:return: bytes"""
        tmp = 0x00
        if 1 in self.channels:
            tmp += 0x03
        if 2 in self.channels:
            tmp += 0x0C
        return bytes([COMMAND_CODE, tmp])


@register(COMMAND_CODE, ["VMBDALI", "VMBDALI-20"])
class ChannelNameRequestMessage3(ChannelNameRequestMessage):
    """Channel Name Request message."""

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        self.channels = data[0]

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.channels])
