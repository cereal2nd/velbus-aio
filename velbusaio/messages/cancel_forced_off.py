"""Cancel Forced Off message class."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import FieldSpec, Message

COMMAND_CODE = 0x13


@register(COMMAND_CODE)
class CancelForcedOff(Message):
    """Cancel Forced Off message."""

    command_code = COMMAND_CODE
    default_priority = PRIORITY_HIGH

    fields = [
        FieldSpec("channel", "B"),
    ]

    validators = [
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Iniatialize Cancel Forced Off message object."""
        super().__init__(address)
        self.channel = 0
