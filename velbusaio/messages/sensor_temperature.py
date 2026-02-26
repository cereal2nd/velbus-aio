"""Sensor Temperature Request Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xE6


@register(COMMAND_CODE)
class SensorTemperatureMessage(Message):
    """Sensor Temperature Message."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Initialize Sensor Temperature Message Object."""
        super().__init__()
        self.cur = 0
        self.min = 0
        self.max = 0

    def getCurTemp(self):
        """Get current temperature."""
        return self.cur

    def getMaxTemp(self):
        """Get maximum temperature."""
        return self.max

    def getMinTemp(self):
        """Get minimum temperature."""
        return self.min

    def populate(self, priority, address, rtr, data):
        """POPULATE the message object with data.

        Data bytes (high + low)
            1 + 2   = current temp
            3 + 4   = min temp
            5 + 6   = max temp
        :return: None
        """
        self.needs_no_rtr(rtr)
        self.needs_data(data, 6)
        self.set_attributes(priority, address, rtr)
        if ((data[0] << 8) | data[1]) >> 15:
            self.cur = -127 + (((data[0] << 8) | data[1]) / 32 * 0.0625)
        else:
            self.cur = (((data[0] << 8) | data[1]) / 32) * 0.0625
        if ((data[2] << 8) | data[3]) >> 15:
            self.min = -127 + (((data[2] << 8) | data[3]) / 32 * 0.0625)
        else:
            self.min = (((data[2] << 8) | data[3]) / 32) * 0.0625
        if ((data[4] << 8) | data[5]) >> 15:
            self.max = -127 + (((data[4] << 8) | data[5]) / 32 * 0.0625)
        else:
            self.max = (((data[4] << 8) | data[5]) / 32) * 0.0625
