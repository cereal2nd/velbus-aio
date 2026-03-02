"""Module Type Message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import MODULE_DIRECTORY, register
from velbusaio.message import Message

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


@register(
    COMMAND_CODE,
    [
        "VMB1BL",
        "VMB6IN",
        "VMB1DM",
        "VMB4RY",
        "VMB2BL",
        "VMB8IR",
        "VMB4PD",
        "VMB1TS",
        "VMB1TC",
        "VMB1LED",
        "VMB4RYLD",
        "VMB4RYNO",
        "VMB4DC",
        "VMBLCDWB",
        "VMBDME",
        "VMBDMI",
        "VMB8PBU",
        "VMB6PBN",
        "VMB2PBN",
        "VMB6PBB",
        "VMB4RF",
        "VMB1RYNO",
        "VMB1BLE",
        "VMB2BLE",
        "VMBGP1",
        "VMBGP2",
        "VMBGP4",
        "VMBGPO",
        "VMB7IN",
        "VMBGPOD",
        "VMB1RYNOS",
        "VMBPIRM",
        "VMBPIRC",
        "VMBPIRO",
        "VMBGP4PIR",
        "VMB1BLS",
        "VMBDMI-R",
        "VMBMETEO",
        "VMB4AN",
        "VMBVP01",
        "VMBEL1",
        "VMBEL2",
        "VMBEL4",
        "VMBELO",
        "VMBELPIR",
        "VMBSIG",
        "VMBGP1-2",
        "VMBGP2-2",
        "VMBGP4-2",
        "VMBGPOD-2",
        "VMBGP4PIR-2",
        "VMCM3",
        "VMBUSBIP",
        "VMB1RYS",
        "VMBKP",
        "VMBIN",
        "VMB4PB",
        "VMBDALI",
    ],
)
class ModuleTypeMessage(Message):
    """Module Type Message."""

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


@register(
    COMMAND_CODE,
    [
        "VMB4RYLD-10",
        "VMB4RYNO-10",
        "VMB2BLE-10",
        "VMB2BLE-20",
        "VMB6PB-20",
        "VMBEL1-20",
        "VMBEL2-20",
        "VMBEL4-20",
        "VMBELO-20",
        "VMBGP1-20",
        "VMBGP2-20",
        "VMBGP4-20",
        "VMBGPO-20",
        "VMBEL4PIR-20",
        "VMBGP4PIR-20",
        "VMB4LEDPWM-20",
        "VMB8IN-20",
        "VMB8DC-20",
        "VMB2DC-20",
        "VMB1RYS-20",
    ],
)
class ModuleType2Message(Message):
    """Module Type Message."""

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
