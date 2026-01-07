"""TempSensorSettingsPart3 message implementation.

:author: Danny De Gaspari
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xC6


@register(COMMAND_CODE)
class TempSensorSettingsPart3(Message):
    """TempSensorSettingsPart3 message class."""

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE])
