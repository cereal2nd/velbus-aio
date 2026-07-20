"""Module Status Request Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ChannelsField, DeclarativeMessage

COMMAND_CODE = 0xFA


@register(COMMAND_CODE)
class ModuleStatusRequestMessage(DeclarativeMessage):
    """Module Status Request Message."""

    _command_code = COMMAND_CODE
    _data_length = 1

    wait_after_send = 500
    channels = ChannelsField(0)

    def data_to_binary(self):
        """:return: bytes"""
        if isinstance(self.channels, list):
            return bytes([COMMAND_CODE, self.channels_to_byte(self.channels)])
        return bytes([COMMAND_CODE, int(self.channels, 16)])
