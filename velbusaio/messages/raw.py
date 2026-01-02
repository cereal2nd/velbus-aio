""":author: Maikel Punie <maikel.punie@gmail.com>"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xA9


@register(COMMAND_CODE, ["VMBMETEO"])
class MeteoRawMessage(Message):
    """send by: VMBMETEO
    received by:
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.rain = 0
        self.light = 0
        self.wind = 0

    def populate(self, priority, address, rtr, data):
        """Data bytes (high + low)
            1 + 2   = current temp
            3 + 4   = min temp
            5 + 6   = max temp
        :return: None
        """
        self.needs_no_rtr(rtr)
        self.needs_data(data, 6)
        self.set_attributes(priority, address, rtr)
        self.rain = (((data[0] << 8) | data[1]) / 32) * 0.1
        self.light = ((data[2] << 8) | data[3]) / 32
        self.wind = (((data[4] << 8) | data[5]) / 32) * 0.1


@register(COMMAND_CODE, ["VMB4AN"])
class SensorRawMessage(Message):
    """send by: VMB4AN
    received by:
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.sensor = 0
        self.mode = 0
        self.value = 0
        self.unit = None

    def populate(self, priority, address, rtr, data):
        self.needs_no_rtr(rtr)
        self.needs_data(data, 5)
        self.set_attributes(priority, address, rtr)
        self.sensor = data[0]
        self.mode = data[1]
        self.value = (data[2] << 16) | (data[3] << 8) | data[4]
        if self.mode == 0:
            self.value = self.value * 0.25
            self.unit = "mV"
        elif self.mode == 1:
            self.value = self.value * 5
            self.unit = "µA"
        elif self.mode == 2:
            self.value = self.value * 0.25
            self.unit = "ohm"
        elif self.mode == 3:
            self.value = self.value * 0.5
            self.unit = "µS"
