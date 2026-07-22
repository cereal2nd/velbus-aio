"""Channel Name Request message.

:author: Thomas Delaet <thomas@delaet.org> and Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    ByteField,
    ChannelsField,
    ComputedField,
    DeclarativeMessage,
)

COMMAND_CODE = 0xEF


@register(COMMAND_CODE)
class ChannelNameRequestMessage(DeclarativeMessage):
    """Channel Name Request message."""

    _command_code = COMMAND_CODE
    _data_length = 1

    channels = ChannelsField(0)

    def data_to_binary(self):
        """:return: bytes"""
        if isinstance(self.channels, list):
            return bytes([COMMAND_CODE, self.channels_to_byte(self.channels)])
        return bytes([COMMAND_CODE, 0xFF])


@register(COMMAND_CODE)
class ChannelNameRequestMessage2(ChannelNameRequestMessage):
    """Channel Name Request message (VMB2BL)."""

    channels = ComputedField(
        parser=lambda data: [
            offset + 1 for offset in range(8) if ((data[0] >> 1) & 0x03) & (1 << offset)
        ],
        default=[],
    )

    def data_to_binary(self):
        """:return: bytes"""
        tmp = 0x00
        if isinstance(self.channels, list):
            if 1 in self.channels:
                tmp += 0x03
            if 2 in self.channels:
                tmp += 0x0C
        return bytes([COMMAND_CODE, tmp])


@register(COMMAND_CODE)
class ChannelNameRequestMessage3(ChannelNameRequestMessage):
    """Channel Name Request message (VMBDALI)."""

    channels = ByteField(0)
