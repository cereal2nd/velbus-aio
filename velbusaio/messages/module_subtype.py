""":author: Thomas Delaet <thomas@delaet.org>"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xB0
COMMAND_CODE_2 = 0xA7
COMMAND_CODE_3 = 0xA6


@register(COMMAND_CODE)
@register(COMMAND_CODE_2)
@register(COMMAND_CODE_3)
class ModuleSubTypeMessage(Message):
    """send by: VMB6IN, VMB4RYLD
    received by:
    """

    # pylint: disable-msg=R0902

    def __init__(self, address=None, sub_address_offset: int = 0) -> None:
        Message.__init__(self)
        self.module_type = 0x00
        self.sub_address_1 = 0xFF
        self.sub_address_2 = 0xFF
        self.sub_address_3 = 0xFF
        self.sub_address_4 = 0xFF
        self.set_defaults(address)
        self.serial = 0
        self.sub_address_offset = sub_address_offset

    def module_name(self) -> str:
        """:return: str"""
        return "Unknown"

    def populate(self, priority, address, rtr, data) -> None:
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        # self.needs_data(data, 6)
        self.set_attributes(priority, address, rtr)
        self.module_type = data[0]
        (self.serial,) = struct.unpack(">L", bytes([0, 0, data[1], data[2]]))
        self.sub_address_1 = data[3]
        self.sub_address_2 = data[4]
        self.sub_address_3 = data[5]
        self.sub_address_4 = data[6]
