"""Set Date Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xB7


@register(COMMAND_CODE)
class SetDate(Message):
    """Set Date Message."""

    def __init__(self, address=0x00, day=None, mon=None, year=None) -> None:
        """Initialize Set Date Message Object."""
        Message.__init__(self)
        self._day = day
        self._mon = mon
        self._year = year
        self.set_defaults(address)

    def set_defaults(self, address) -> None:
        """Set default values."""
        if address is not None:
            self.set_address(address)
        self.set_low_priority()
        self.set_no_rtr()

    def populate(self, priority, address, rtr, data) -> None:
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 4)
        self.set_attributes(priority, address, rtr)
        self._day = data[0]
        self._mon = data[1]
        self._year = (data[2] << 8) + data[3]

    def data_to_binary(self) -> bytes:
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self._day,
                self._mon,
                (self._year >> 8),
                (self._year & 0x00FF),
            ]
        )
