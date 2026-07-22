"""Channel Name Part 2 message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    BitField,
    ByteField,
    ChannelField,
    DeclarativeMessage,
    StringField,
)

COMMAND_CODE = 0xF1


@register(COMMAND_CODE)
class ChannelNamePart2Message(DeclarativeMessage):
    """Channel Name Part 2 message."""

    _command_code = COMMAND_CODE
    _data_length = 7

    channel = ChannelField(0)
    name = StringField(1)


@register(COMMAND_CODE)
class ChannelNamePart2Message2(ChannelNamePart2Message):
    """Channel Name Part 2 message (integer channel)."""

    _generates_data_to_binary = False

    channel = ByteField(0)


@register(COMMAND_CODE)
class ChannelNamePart2Message3(ChannelNamePart2Message):
    """Channel Name Part 2 message (VMB1BL/VMB2BL)."""

    _data_length = 5
    _generates_data_to_binary = False

    channel = BitField(0, mask=0x06, shift=1)
