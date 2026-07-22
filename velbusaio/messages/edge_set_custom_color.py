"""Edge Set Custom Color message class.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import BitField, ByteField, DeclarativeMessage

COMMAND_CODE = 0xD4


@register(COMMAND_CODE)
class EdgeSetCustomColor(DeclarativeMessage):
    """Edge Set Custom Color message."""

    _command_code = COMMAND_CODE
    _priority = None

    pallet = ByteField(0, default=31)
    rgb = BitField(1, 0x80, as_bool=True, default=False)
    saturation = BitField(1, 0x7F, default=0)
    red = ByteField(2)
    green = ByteField(3)
    blue = ByteField(4)

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
