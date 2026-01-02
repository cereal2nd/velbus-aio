""":author: Maikel Punie <maikel.punie@gmail.com>"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xE7


@register(COMMAND_CODE)
class SensorSettingsRequestMessage(Message):
    """send by:
    received by: VMB6IN, VMB4RYLD
    """

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_rtr(rtr)
        self.needs_no_data(data)
        self.set_attributes(priority, address, rtr)

    def set_defaults(self, address):
        self.set_address(address)
        self.set_low_priority()
        self.set_rtr()

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([])
