"""Set Date Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import FieldSpec, Message

COMMAND_CODE = 0xB7


@register(COMMAND_CODE)
class SetDate(Message):
    """Set Date Message."""

    command_code = COMMAND_CODE
    fields = [
        FieldSpec("_day", "B"),
        FieldSpec("_mon", "B"),
        FieldSpec("_year", "H"),
    ]

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=0x00, day=None, mon=None, year=None) -> None:
        """Initialize Set Date Message Object."""
        super().__init__()
        self._day = day
        self._mon = mon
        self._year = year
        self.set_defaults(address)
