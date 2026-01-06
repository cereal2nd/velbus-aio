"""Set Temperature Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xE4


@register(COMMAND_CODE)
class SetTemperatureMessage(Message):
    """Set Temperature Message."""

    def __init__(self, address=None):
        """Initialize Set Temperature Message Object."""
        Message.__init__(self)
        self.temp_type = 0x00
        self.temp = 0x00
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)

        self.temp_type = 0x00
        self.temp = data[1] * 2

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, int(self.temp_type), int(self.temp)])
