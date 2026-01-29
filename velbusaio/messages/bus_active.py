"""Bus Active message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import Message

COMMAND_CODE = 0x0A


@register(COMMAND_CODE)
class BusActiveMessage(Message):
    """Bus Active message."""

    command_code = COMMAND_CODE
    fields = []
    default_priority = PRIORITY_HIGH

    validators = [
        lambda self: self.needs_high_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Bus Active message."""
        super().__init__()
        self.set_defaults(address)
