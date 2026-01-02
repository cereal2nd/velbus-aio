""":author: Thomas Delaet <thomas@delaet.org>"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0x0C


@register(COMMAND_CODE)
class ReceiveReadyMessage(Message):
    """send by:
    received by: VMB1USB
    """

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        # self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_no_data(data)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE])
