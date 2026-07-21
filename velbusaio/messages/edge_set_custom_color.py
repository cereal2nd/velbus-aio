"""Edge Set Custom Color message class.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage

COMMAND_CODE = 0xD4


@register(COMMAND_CODE)
class EdgeSetCustomColor(DeclarativeMessage):
    """Edge Set Custom Color message."""

    _command_code = COMMAND_CODE
    _priority = None

    pallet = ByteField(0, default=31)
    red = ByteField(2)
    green = ByteField(3)
    blue = ByteField(4)

    def __init__(self, address=None):
        """Initialize Edge Set Custom Color message."""
        super().__init__(address)
        self.rgb = False
        self.saturation = 0

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)
        self.pallet = data[0]
        self.rgb = bool(data[1] & 0x80)
        self.saturation = data[1] & 0x7F
        self.red = data[2]
        self.green = data[3]
        self.blue = data[4]

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.pallet,
                ((self.rgb << 7) + self.saturation),
                self.red,
                self.green,
                self.blue,
            ]
        )
