"""Counter Status Request message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xBD


@register(COMMAND_CODE)
class CounterStatusRequestMessage(DeclarativeMessage):
    """Counter Status Request message."""

    _command_code = COMMAND_CODE
    _data_length = 2

    wait_after_send = 500

    def __init__(self, address: int | None = None) -> None:
        """Initialize Counter Status Request message."""
        Message.__init__(self)
        self.channels: list[int] = []
        self.set_defaults(address)

    def data_to_binary(self) -> bytes:
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.channels_to_byte(self.channels), 0x00])
