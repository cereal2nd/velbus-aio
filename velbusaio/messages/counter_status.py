"""Counter Status message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from typing import cast

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    ComputedField,
    DeclarativeMessage,
    Field,
    Int16Field,
    Int32Field,
)
from velbusaio.messages.counter_rate import compute_counter_kwh_watt

COMMAND_CODE = 0xBE


@register(COMMAND_CODE)
class CounterStatusMessage(DeclarativeMessage):
    """Counter Status message.

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
        self.kwh, self.watt = compute_counter_kwh_watt(
            self.counter, self.pulses, self.delay
        )

    def get_channels(self) -> int | list[int]:
        """:return: channel number or list of channel numbers"""
        return cast("int | list[int]", self.channel)
