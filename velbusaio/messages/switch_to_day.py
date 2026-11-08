"""Switch to day message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xDC


@register(COMMAND_CODE)
class SwitchToDayMessage(DeclarativeMessage):
    """Switch to day message class."""

    _command_code = COMMAND_CODE
    _priority = None

    def __init__(self, address: int | None = None, sleep: int = 0) -> None:
        """Initialize SwitchToDayMessage instance."""
        super().__init__(address)
        self.sleep = sleep

    def data_to_binary(self) -> bytes:
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.sleep >> 8, self.sleep & 0xFF])
