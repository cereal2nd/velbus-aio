"""Bus Error Counter Status message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xDA


@register(COMMAND_CODE)
class BusErrorCounterStatusMessage(Message):
    """Bus Error Counter Status message."""

    def __init__(self, address=None):
        """Initialize Bus Error Counter Status message."""
        Message.__init__(self)
        self.transmit_error_counter = 0
        self.receive_error_counter = 0
        self.bus_off_counter = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 3)
        self.transmit_error_counter = data[0]
        self.receive_error_counter = data[1]
        self.bus_off_counter = data[2]

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.transmit_error_counter,
                self.receive_error_counter,
                self.bus_off_counter,
            ]
        )
