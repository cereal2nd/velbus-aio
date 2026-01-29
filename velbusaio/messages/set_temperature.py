"""Set Temperature Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import FieldSpec, Message

COMMAND_CODE = 0xE4


@register(COMMAND_CODE)
class SetTemperatureMessage(Message):
    """Set Temperature Message."""

    command_code = COMMAND_CODE
    fields = [
        FieldSpec("temp_type", "B"),
        FieldSpec("temp", "B", decode=lambda x: x * 2),
    ]

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Set Temperature Message Object."""
        super().__init__()
        self.temp_type = 0x00
        self.temp = 0x00
        self.set_defaults(address)

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, int(self.temp_type), int(self.temp)])
