"""Set Daylight Saving Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xAF


@register(COMMAND_CODE)
class SetDaylightSaving(Message):
    """Set Daylight Saving Message."""

    def __init__(self, address=0x00, ds=None) -> None:
        """Initialize Set Daylight Saving Message Object."""
        Message.__init__(self)
        self._ds = ds
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
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        self._ds = data[0]

    def data_to_binary(self) -> bytes:
        """:return: bytes"""
        return bytes([COMMAND_CODE, self._ds])
