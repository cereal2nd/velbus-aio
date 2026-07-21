"""Module Type Message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import MODULE_DIRECTORY, register
from velbusaio.message import Message
from velbusaio.message_fields import DeclarativeMessage

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


@register(COMMAND_CODE)
class ModuleTypeMessage(DeclarativeMessage):
    """Module Type Message."""

    _command_code = COMMAND_CODE
    _generates_data_to_binary = False

    def __init__(self, address=None) -> None:
        """Initialize Module Type Message object."""
        Message.__init__(self)
        self.module_type = 0x00
        self.led_on = []
        self.led_slow_blinking = []
        self.led_fast_blinking = []
        self.serial = 0
        self.memory_map_version = 0
        self.build_year = 0
        self.build_week = 0
        self.set_defaults(address)

    def module_type_name(self) -> str:
        """:return: str"""
        return MODULE_DIRECTORY.get(self.module_type, "Unknown")

    def populate(self, priority, address, rtr, data) -> None:
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)
        self.module_type = data[0]
        if data[0] not in MODULES_WITHOUT_SERIAL:
            (self.serial,) = struct.unpack(">L", bytes([0, 0, data[1], data[2]]))
            self.memory_map_version = data[3]
        self.build_year = data[-2]
        self.build_week = data[-1]


@register(COMMAND_CODE)
class ModuleType2Message(DeclarativeMessage):
    """Module Type Message."""

    _command_code = COMMAND_CODE
    _generates_data_to_binary = False

    def __init__(self, address=None) -> None:
        """Initialize Module Type Message object."""
        Message.__init__(self)
        self.module_type = 0x00
        self.led_on = []
        self.led_slow_blinking = []
        self.led_fast_blinking = []
        self.serial = 0
        self.memory_map_version = 0
        self.build_year = 0
        self.build_week = 0
        self.term = 0
        self.set_defaults(address)

    def module_name(self) -> str:
        """:return: str"""
        return "Unknown"

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)
        self.module_type = data[0]
        if data[0] not in MODULES_WITHOUT_SERIAL:
            (self.serial,) = struct.unpack(">L", bytes([0, 0, data[1], data[2]]))
            self.memory_map_version = data[3]
        self.build_year = data[-3]
        self.build_week = data[-2]
        self.term = data[-1]
