"""PSU Load Message.

:author: Maikel Punie
"""

from __future__ import annotations

import struct

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xA2
BALANCED = 0x01
BOOST = 0x02
BACKUP = 0x03


@register(COMMAND_CODE, ["VMBPSUMNGR-20"])
class PsuLoadMessage(Message):
    """PSU Load Message."""

    def __init__(self, address=None):
        """Initialize PSU Load Message Object."""
        Message.__init__(self)
        self.mode = 0
        self.load_1 = 0
        self.load_2 = 0
        self.out = 0

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 3)
        self.set_attributes(priority, address, rtr)
        self.mode = data[0]
        self.load_1 = data[1]
        self.load_2 = data[2]
        self.out = data[3]

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
