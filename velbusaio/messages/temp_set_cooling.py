""":author: Thomas Delaet <thomas@delaet.org>"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xDF


@register(COMMAND_CODE)
class TempSetCoolingMessage(Message):
    """send by:
    received by: VMB4RYLD
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, 0xAA])
