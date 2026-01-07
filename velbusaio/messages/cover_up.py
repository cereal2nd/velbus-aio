"""Cover Up message.

:author: Tom Dupré <gitd8400@gmail.com>
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0x05


@register(COMMAND_CODE, ["VMB1BLE", "VMB2BLE", "VMB1BLS", "VMB2BLE-10"])
class CoverUpMessage(Message):
    """Cover Up message."""

    def __init__(self, address=None):
        """Initialize Cover Up message."""
        Message.__init__(self)
        self.channel = 0
        self.delay_time = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 4)
        self.set_attributes(priority, address, rtr)
        self.channel = self.byte_to_channel(data[0])
        (self.delay_time,) = struct.unpack(">L", bytes([0]) + data[1:])

    def set_defaults(self, address):
        """Logic to set default values."""
        if address is not None:
            self.set_address(address)
        self.set_high_priority()
        self.set_no_rtr()

    def data_to_binary(self):
        """:return: bytes"""
        return (
            bytes([COMMAND_CODE, self.channels_to_byte([self.channel])])
            + struct.pack(">L", self.delay_time)[-3:]
        )


@register(COMMAND_CODE, ["VMB1BL", "VMB2BL"])
class CoverUpMessage2(Message):
    """Cover Up message."""

    def __init__(self, address=None):
        """Initialize Cover Up message."""
        Message.__init__(self)
        self.channel = 0
        self.delay_time = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 4)
        self.set_attributes(priority, address, rtr)
        # 00000011 = channel 1
        # 00001100 = channel 2
        # so shift 1 bit to the right + and with 03
        tmp = (data[0] >> 1) & 0x03
        self.channel = self.byte_to_channel(tmp)
        (self.delay_time,) = struct.unpack(">L", bytes([0]) + data[1:])

    def set_defaults(self, address):
        """Logic to set default values."""
        if address is not None:
            self.set_address(address)
        self.set_high_priority()
        self.set_no_rtr()

    def data_to_binary(self):
        """:return: bytes"""
        if self.channel == 0x01:
            tmp = 0x03
        else:
            tmp = 0x0C
        return bytes([COMMAND_CODE, tmp]) + struct.pack(">L", self.delay_time)[-3:]
