"""Set realtime Clock Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xD8


@register(COMMAND_CODE)
class SetRealtimeClock(Message):
    """Set realtime Clock Message."""

    def __init__(self, address=0x00, wday=None, hour=None, min=None) -> None:
        """Initialize Set realtime Clock Message Object."""
        Message.__init__(self)
        self._wday = wday
        self._hour = hour
        self._min = min
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
        self.needs_data(data, 3)
        self.set_attributes(priority, address, rtr)
        self._wday = data[0]
        self._hour = data[1]
        self._min = data[2]

    def data_to_binary(self) -> bytes:
        """:return: bytes"""
        return bytes([COMMAND_CODE, self._wday, self._hour, self._min])
