"""Module SubType Message class.

author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, ComputedField, DeclarativeMessage, Field

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
    sub_address_offset = Field(default=0, serializable=False)

    def module_name(self) -> str:
        """:return: str"""
        return "Unknown"
