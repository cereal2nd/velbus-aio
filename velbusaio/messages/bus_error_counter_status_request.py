"""Bus Error Counter Status Request message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xD9


@register(COMMAND_CODE)
class BusErrorStatusRequestMessage(Message):
    """Bus Error Counter Status Request message."""

    command_code = COMMAND_CODE
    fields = []

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Bus Error Counter Status Request message."""
        super().__init__()
        self.set_defaults(address)
