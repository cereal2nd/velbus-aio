"""PSU Values Message.

:author: Maikel Punie
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xA3


@register(COMMAND_CODE, ["VMBPSUMNGR-20"])
class PsuValuesMessage(Message):
    """PSU Values Message."""

    def __init__(self, address=None):
        """Initialize PSU Values Message Object."""
        Message.__init__(self)
        self.channel = 0
        self.watt = 0
        self.volt = 0
        self.amp = 0

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 3)
        self.set_attributes(priority, address, rtr)
        self.channel = (data[0] & 0xF0) >> 4
        self.watt = ((data[0] & 0x0F) << 16 | data[1] << 8 | data[2]) / 1000
        self.volt = (data[3] << 8 | data[4]) / 1000
        self.amp = (data[5] << 8 | data[6]) / 1000

    def data_to_binary(self):
        """:return: bytes"""
        return (
            bytes(
                [
                    COMMAND_CODE,
                    self.mode,
                    self.load_1,
                    self.load_2,
                    self.out,
                ]
            )
            + struct.pack(">L", self.delay_time)[-3:]
        )
