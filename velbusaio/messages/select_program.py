"""Select Program Message.

:author: Danny De Gaspari
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import FieldSpec, Message

COMMAND_CODE = 0xB3


@register(COMMAND_CODE)
class SelectProgramMessage(Message):
    """Select Program Message."""

    command_code = COMMAND_CODE
    fields = [
        FieldSpec("select_program", "B", decode=lambda x: x & 0x03, encode=lambda x: x & 0x03),
    ]

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None, program=0):
        """Initialize Select Program Message Object."""
        super().__init__()
        self.select_program = program
        self.set_defaults(address)
