"""Light Value Request message class.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xAA


@register(COMMAND_CODE)
class LightValueRequest(Message):
    """Light Value Request message."""

    command_code = COMMAND_CODE
    fields = []

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Light Value Request message."""
        super().__init__()
        self.set_defaults(address)
