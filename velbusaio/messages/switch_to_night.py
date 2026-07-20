"""Switch to night message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xDD


@register(COMMAND_CODE)
class SwitchToNightMessage(DeclarativeMessage):
    """Switch to night message."""

    _command_code = COMMAND_CODE
    _priority = None

    def __init__(self, address=None, sleep=0):
        """Initialize SwitchToNightMessage instance."""
        super().__init__(address)
        self.sleep = sleep

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.sleep >> 8, self.sleep & 0xFF])
