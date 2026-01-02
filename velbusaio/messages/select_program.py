""":author: Danny De Gaspari"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xB3


@register(COMMAND_CODE)
class SelectProgramMessage(Message):
    def __init__(self, address=None, program=0):
        Message.__init__(self)
        self.select_program = program
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)

        self.select_program = data[0] & 0x03

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.select_program])
