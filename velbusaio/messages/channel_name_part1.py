"""Channel Name Part 1 message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xF0


@register(COMMAND_CODE)
class ChannelNamePart1Message(DeclarativeMessage):
    """Channel Name Part 1 message."""

    _command_code = COMMAND_CODE
    _priority = "low"

    def __init__(self, address=None):
        """Initialize Channel Name Part 1 message."""
        super().__init__(address)
        self.channel = 0
        self.name = ""

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        channels = self.byte_to_channels(data[0])
        self.needs_one_channel(channels)
        self.channel = channels[0]
        self.name = "".join([chr(x) for x in data[1:]])

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.channels_to_byte([self.channel])]) + bytes(
            self.name, "ascii", "ignore"
        )


@register(COMMAND_CODE)
class ChannelNamePart1Message2(ChannelNamePart1Message):
    """Chnannel Name Part 1 message."""

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.channel = data[0]
        self.name = "".join([chr(x) for x in data[1:]])


@register(COMMAND_CODE)
class ChannelNamePart1Message3(ChannelNamePart1Message):
    """Channel Name Part 1 message."""

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 5)
        self.set_attributes(priority, address, rtr)
        self.channel = (data[0] >> 1) & 0x03
        self.name = "".join([chr(x) for x in data[1:]])
