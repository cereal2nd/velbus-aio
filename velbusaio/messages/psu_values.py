"""PSU Values Message.

:author: Maikel Punie
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ComputedField, DeclarativeMessage

COMMAND_CODE = 0xA3


@register(COMMAND_CODE)
class PsuValuesMessage(DeclarativeMessage):
    """PSU Values Message."""

    _command_code = COMMAND_CODE
    _data_length = 7

    channel = ComputedField(parser=lambda data: (data[0] & 0xF0) >> 4, default=0)
    watt = ComputedField(
        parser=lambda data: ((data[0] & 0x0F) << 16 | data[1] << 8 | data[2]) / 1000,
        default=0,
    )
    volt = ComputedField(parser=lambda data: (data[3] << 8 | data[4]) / 1000, default=0)
    amp = ComputedField(parser=lambda data: (data[5] << 8 | data[6]) / 1000, default=0)

    def data_to_binary(self):
        """:return: bytes"""
        watt = int(round(self.watt * 1000))
        volt = int(round(self.volt * 1000))
        amp = int(round(self.amp * 1000))
        return bytes(
            [
                COMMAND_CODE,
                ((self.channel & 0x0F) << 4) | ((watt >> 16) & 0x0F),
                (watt >> 8) & 0xFF,
                watt & 0xFF,
                (volt >> 8) & 0xFF,
                volt & 0xFF,
                (amp >> 8) & 0xFF,
                amp & 0xFF,
            ]
        )
