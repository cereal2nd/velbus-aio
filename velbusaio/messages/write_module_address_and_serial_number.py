"""Write Module Address And Serial Number Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0x6A


@register(COMMAND_CODE)
class WriteModuleAddressAndSerialNumberMessage(Message):
    """Write Module Address And Serial Number Message."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize WriteModuleAddressAndSerialNumberMessage class."""
        super().__init__()
        self.module_type = 0x00
        self.current_serial = 0
        self.module_address = 0x00
        self.new_serial = 0
        self.set_defaults(address)

    def set_defaults(self, address):
        """Set the default values."""
        if address is not None:
            self.set_address(address)
        self.set_firmware_priority()
        self.set_no_rtr()

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_firmware_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 6)
        self.set_attributes(priority, address, rtr)
        self.module_type = data[0]
        prefix = bytes([0, 0])
        (self.current_serial,) = struct.unpack(">L", prefix + data[1] + data[2])
        self.module_address = data[3]
        (self.new_serial,) = struct.unpack(">L", prefix + data[4] + data[5])

    def data_to_binary(self):
        """:return: bytes"""
        return (
            chr(COMMAND_CODE)
            + chr(self.module_type)
            + struct.pack(">L", self.current_serial)[2:]
            + chr(self.module_address)
            + struct.pack(">L", self.new_serial)[2:]
        )
