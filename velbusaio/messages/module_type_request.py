"""Module Type Request Message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.message import Message


class ModuleTypeRequestMessage(Message):
    """Module Type Request Message."""

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_rtr(rtr)
        self.needs_no_data(data)
        self.set_attributes(priority, address, rtr)

    def set_defaults(self, address):
        """Set defaults."""
        if address is not None:
            self.set_address(address)
        self.set_low_priority()
        self.set_rtr()

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([])
