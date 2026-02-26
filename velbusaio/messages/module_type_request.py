"""Module Type Request Message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.message import Message


class ModuleTypeRequestMessage(Message):
    """Module Type Request Message."""

    default_rtr = True

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Module Type Request message."""
        super().__init__()
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_rtr(rtr)
        self.needs_no_data(data)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([])
