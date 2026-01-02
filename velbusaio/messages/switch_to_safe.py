""":author: Thomas Delaet <thomas@delaet.org>"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xDE


@register(COMMAND_CODE)
class SwitchToSafeMessage(Message):
    """send by:
    received by: VMB4RYLD
    """

    def __init__(self, address=None, sleep=0):
        Message.__init__(self)
        self.sleep = sleep
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.sleep >> 8, self.sleep & 0xFF])
