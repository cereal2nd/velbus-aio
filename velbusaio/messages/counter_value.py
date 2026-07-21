"""Counter Value message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xA4


@register(COMMAND_CODE)
class CounterValueMessage(DeclarativeMessage):
    """Counter Value message."""

    _command_code = COMMAND_CODE
    _priority = None
    _data_length = 7
    _generates_data_to_binary = False

    def __init__(self, address=None):
        """Initialize Counter Value message."""
        Message.__init__(self)
        self.channel = 0
        self.power = 0
        self.energy = 0

    def populate(self, priority, address, rtr, data):
        """Parses the received data.

        Manual VMB8IN-20:
        DATABYTE2 bits 7-4 = Counter channel 1 to 8 (0-7)
        DATABYTE2 bits 3-0 = Highest nibble (bits 19…16) of Power
        DATABYTE3 = high byte of power
        DATABYTE4 = low byte of power
        DATABYTE5 = MSB of energy counter
        DATABYTE6 = upper byte of energy counter
        DATABYTE7 = high byte of energy counter
        DATABYTE8 = LSB of energy counter
        :return: None
        """
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.channel = (data[0] >> 4) + 1
        self.power = ((data[0] & 0x0F) << 16) + (data[1] << 8) + data[2]
        self.energy = (data[3] << 24) + (data[4] << 16) + (data[5] << 8) + data[6]

    def get_channels(self):
        """:return: list"""
        return self.channel
