"""Module Type Message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import MODULE_DIRECTORY, register
from velbusaio.message_fields import ByteField, ComputedField, DeclarativeMessage, Field

COMMAND_CODE = 0xFF
MODULES_WITHOUT_SERIAL = {
    0x01: "VMB8PB",
    0x02: "VMB1RY",
    0x03: "VMB1BL",
    0x05: "VMB6IN",
    0x07: "VMB1DM",
    0x08: "VMB4RY",
    0x09: "VMB2BL",
    0x0C: "VMB1TS",
    0x0E: "VMB1TC",
    0x0F: "VMB1LED",
    0x14: "VMBDME",
}


def _parse_serial(data: bytes) -> int:
    """Parse the serial number when the module reports one."""
    if data[0] in MODULES_WITHOUT_SERIAL:
        return 0
    (serial,) = struct.unpack(">L", bytes([0, 0, data[1], data[2]]))
    return serial


@register(COMMAND_CODE)
class ModuleTypeMessage(DeclarativeMessage):
    """Module Type Message."""

    _command_code = COMMAND_CODE
    _generates_data_to_binary = False

    module_type = ByteField(0)
    serial = ComputedField(parser=_parse_serial, default=0)
    memory_map_version = ComputedField(
        parser=lambda data: data[3] if data[0] not in MODULES_WITHOUT_SERIAL else 0,
        default=0,
    )
    build_year = ComputedField(parser=lambda data: data[-2], default=0)
    build_week = ComputedField(parser=lambda data: data[-1], default=0)
    led_on = Field(default=[], serializable=False)
    led_slow_blinking = Field(default=[], serializable=False)
    led_fast_blinking = Field(default=[], serializable=False)

    def module_type_name(self) -> str:
        """:return: str"""
        return MODULE_DIRECTORY.get(self.module_type, "Unknown")


@register(COMMAND_CODE)
class ModuleType2Message(DeclarativeMessage):
    """Module Type Message."""

    _command_code = COMMAND_CODE
    _generates_data_to_binary = False

    module_type = ByteField(0)
    serial = ComputedField(parser=_parse_serial, default=0)
    memory_map_version = ComputedField(
        parser=lambda data: data[3] if data[0] not in MODULES_WITHOUT_SERIAL else 0,
        default=0,
    )
    build_year = ComputedField(parser=lambda data: data[-3], default=0)
    build_week = ComputedField(parser=lambda data: data[-2], default=0)
    term = ComputedField(parser=lambda data: data[-1], default=0)
    led_on = Field(default=[], serializable=False)
    led_slow_blinking = Field(default=[], serializable=False)
    led_fast_blinking = Field(default=[], serializable=False)

    def module_name(self) -> str:
        """:return: str"""
        return "Unknown"
