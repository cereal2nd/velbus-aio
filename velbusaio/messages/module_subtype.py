"""Module SubType Message class.

author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message import Message
from velbusaio.message_fields import ByteField, ComputedField, DeclarativeMessage

COMMAND_CODE = 0xB0
COMMAND_CODE_2 = 0xA7
COMMAND_CODE_3 = 0xA6


@register(COMMAND_CODE)
@register(COMMAND_CODE_2)
@register(COMMAND_CODE_3)
class ModuleSubTypeMessage(DeclarativeMessage):
    """Module SubType Message."""

    _command_code = COMMAND_CODE
    _generates_data_to_binary = False

    module_type = ByteField(0)
    serial = ComputedField(
        parser=lambda data: struct.unpack(">L", bytes([0, 0, data[1], data[2]]))[0],
        default=0,
    )
    sub_address_1 = ByteField(3, default=0xFF)
    sub_address_2 = ByteField(4, default=0xFF)
    sub_address_3 = ByteField(5, default=0xFF)
    sub_address_4 = ByteField(6, default=0xFF)

    def __init__(self, address=None, sub_address_offset: int = 0) -> None:
        """Initialize Module SubType Message object."""
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
