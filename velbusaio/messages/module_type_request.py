"""Module Type Request Message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.message_fields import DeclarativeMessage


class ModuleTypeRequestMessage(DeclarativeMessage):
    """Module Type Request Message."""

    _priority = "low"
    _rtr = True
    _data_length = 0
    _generates_data_to_binary = False

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_rtr(rtr)
        self.needs_no_data(data)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([])
