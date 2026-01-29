"""Memory Data Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import FieldSpec, Message

COMMAND_CODE = 0xFE


@register(COMMAND_CODE)
class MemoryDataMessage(Message):
    """Memory Data Message."""

    command_code = COMMAND_CODE
    fields = [
        FieldSpec("high_address", "B"),
        FieldSpec("low_address", "B"),
        FieldSpec("data", "B"),
    ]

    # Message-level validators for priority/rtr
    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Memory Data Message object."""
        super().__init__()
        self.high_address = 0x00
        self.low_address = 0x00
        self.data = 0
        self.set_defaults(address)

