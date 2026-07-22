"""Kwh Status message class.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    ComputedField,
    DeclarativeMessage,
    Field,
    Int16Field,
    Int32Field,
)

COMMAND_CODE = 0xBE


@register(COMMAND_CODE)
class KwhStatusMessage(DeclarativeMessage):
    """Kwh Status message.

    -DB1    last 2 bits   = channel
    -DB1    first 6 bits  = pulses
    -DB2-5                = pulse counter
    -DB6-7                = ms/pulse
    """

    _command_code = COMMAND_CODE
    _priority = None
    _data_length = 7
    _generates_data_to_binary = False

    channel = ComputedField(parser=lambda data: (data[0] & 0x03) + 1, default=0)
    pulses = ComputedField(parser=lambda data: (data[0] >> 2) * 100, default=0)
    counter = Int32Field(1)
    delay = Int16Field(5)
    kwh = Field(default=0, serializable=False)
    watt = Field(default=0, serializable=False)

    def _post_populate(self, data: bytes) -> None:
        self.kwh = float(float(self.counter) / self.pulses)
        self.watt = float((1000 * 1000 * 3600) / (self.delay * self.pulses))
        if self.watt < 55:
            self.watt = 0

    def get_channels(self):
        """:return: list"""
        return self.channel
