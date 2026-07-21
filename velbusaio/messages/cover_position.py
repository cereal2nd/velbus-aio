"""Cover Position message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, ChannelField, DeclarativeMessage

COMMAND_CODE = 0x1C


@register(COMMAND_CODE)
class CoverPosMessage(DeclarativeMessage):
    """Cover Position message."""

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 2

    channel = ChannelField(0)
    position = ByteField(1)
