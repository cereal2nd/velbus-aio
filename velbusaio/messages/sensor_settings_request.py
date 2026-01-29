"""Sensor Settings Request Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xE7


@register(COMMAND_CODE)
class SensorSettingsRequestMessage(Message):
    """Sensor Settings Request Message."""

    command_code = COMMAND_CODE
    default_rtr = True

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Sensor Settings Request message."""
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
