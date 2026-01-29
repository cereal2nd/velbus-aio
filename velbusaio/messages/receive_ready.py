"""Receive Ready Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0x0C


@register(COMMAND_CODE)
class ReceiveReadyMessage(Message):
    """Receive Ready Message."""

    command_code = COMMAND_CODE
    fields = []

    validators = [
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Receive Ready message."""
        super().__init__()
        self.set_defaults(address)
