"""Set Date Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage, Int16Field

COMMAND_CODE = 0xB7


@register(COMMAND_CODE)
class SetDate(DeclarativeMessage):
    """Set Date Message."""

    _command_code = COMMAND_CODE
    _data_length = 4

    _day = ByteField(0, default=None)
    _mon = ByteField(1, default=None)
    _year = Int16Field(2, default=None)

    def __init__(self, address=0x00, day=None, mon=None, year=None) -> None:
        """Initialize Set Date Message Object."""
        super().__init__(address)
        if day is not None:
            self._day = day
        if mon is not None:
            self._mon = mon
        if year is not None:
            self._year = year
