"""Counter Status Request message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xBD


@register(COMMAND_CODE, ["VMB7IN", "VMB8IN-20"])
class CounterStatusRequestMessage(DeclarativeMessage):
    """Counter Status Request message."""

    _command_code = COMMAND_CODE
    _data_length = 2

    wait_after_send = 500

    def __init__(self, address=None):
        """Initialize Counter Status Request message."""
        Message.__init__(self)
        self.channels = []
        self.set_defaults(address)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.channels_to_byte(self.channels), 0x00])
