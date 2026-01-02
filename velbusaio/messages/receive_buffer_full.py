""":author: Thomas Delaet <thomas@delaet.org>"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0x0B


@register(COMMAND_CODE)
class ReceiveBufferFullMessage(Message):
    """send by:
    received by: VMB1USB
    """

    def set_defaults(self, address):
        if address is not None:
            self.set_address(address)
        self.set_high_priority()
        self.set_no_rtr()

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_no_data(data)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE])
