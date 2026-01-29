"""Bus Off message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0x09


@register(COMMAND_CODE)
class BusOffMessage(Message):
    """Bus Off message."""

    command_code = COMMAND_CODE
    fields = []

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Bus Off message."""
        super().__init__()
        self.set_defaults(address)
