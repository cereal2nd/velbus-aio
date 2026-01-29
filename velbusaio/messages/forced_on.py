"""Forced On message class."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import FieldSpec, Message

COMMAND_CODE = 0x14


@register(COMMAND_CODE)
class ForcedOn(Message):
    """Forced On message."""

    command_code = COMMAND_CODE
    default_priority = PRIORITY_HIGH

    fields = [
        FieldSpec("channel", "B"),
        FieldSpec("delay_time", "3s", decode=lambda x: int.from_bytes(x, "big"), encode=lambda x: x.to_bytes(3, "big")),
    ]

    validators = [
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Iniatialize Forced On message object."""
        super().__init__(address)
        self.channel = 0
        self.delay_time = 0
