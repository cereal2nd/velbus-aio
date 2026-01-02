""":author: Maikel Punie <maikel.punie@gmail.com>"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xA4


@register(COMMAND_CODE, ["VMB8IN-20"])
class CounterValueMessage(Message):
    def __init__(self, address=None):
        Message.__init__(self)
        self.channel = 0
        self.power = 0
        self.energy = 0

    def populate(self, priority, address, rtr, data):
        """-DB0    bit 0-4      = channel
        -DB0   bit 5-7      = Highest nibble (bits 19…16) of Power
        -DB1                 = bits 15…8 of Power
        -DB2                 = bits 7…0 of Power
        -DB3    bit 0-7      = energy counter
        -DB4    bit 0-7      = energy counter
        -DB5    bit 0-7      = energy counter
        :return: None
        """
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.channel = (data[0] & 0x0F0) + 1
        self.power = (data[0] << 16) + (data[1] << 8) + data[2]
        self.energy = (data[3] << 16) + (data[4] << 8) + data[5]

    def get_channels(self):
        """:return: list"""
        return self.channel
