"""Kwh Status message class.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xBE


@register(COMMAND_CODE)
class KwhStatusMessage(Message):
    """Kwh Status message."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize Kwh Status message."""
        super().__init__()
        self.channel = 0
        self.pulses = 0
        self.counter = 0
        self.kwh = 0
        self.delay = 0
        self.watt = 0

    def populate(self, priority, address, rtr, data):
        """Parses the Kwh Status message.

        -DB1    last 2 bits   = channel
        -DB1    first 6 bist  = pulses
        -DB2-5                = pulse counter
        -DB6-7                = ms/pulse
        :return: None
        """
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.channel = (data[0] & 0x03) + 1
        self.pulses = (data[0] >> 2) * 100
        self.counter = (data[1] << 24) + (data[2] << 16) + (data[3] << 8) + data[4]
        self.kwh = float(float(self.counter) / self.pulses)
        self.delay = (data[5] << 8) + data[6]
        self.watt = float((1000 * 1000 * 3600) / (self.delay * self.pulses))
        if self.watt < 55:
            self.watt = 0

    def get_channels(self):
        """:return: list"""
        return self.channel
