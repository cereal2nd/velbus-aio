"""Push Button Status Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ChannelsField, DeclarativeMessage

COMMAND_CODE = 0x00


@register(COMMAND_CODE)
class PushButtonStatusMessage(DeclarativeMessage):
    """Push Button Status Message."""

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 3

    closed = ChannelsField(0)
    opened = ChannelsField(1)
    closed_long = ChannelsField(2)

    def get_channels(self):
        """:return: list"""
        return self.closed + self.opened
