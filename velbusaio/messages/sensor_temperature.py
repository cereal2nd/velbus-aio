"""Sensor Temperature Request Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage, TemperatureField

COMMAND_CODE = 0xE6


@register(COMMAND_CODE)
class SensorTemperatureMessage(DeclarativeMessage):
    """Sensor Temperature Message."""

    _command_code = COMMAND_CODE
    _priority = None
    _data_length = 6
    _generates_data_to_binary = False

    cur = TemperatureField(0)
    min = TemperatureField(2)
    max = TemperatureField(4)

    def getCurTemp(self):
        """Get current temperature."""
        return self.cur

    def getMaxTemp(self):
        """Get maximum temperature."""
        return self.max

    def getMinTemp(self):
        """Get minimum temperature."""
        return self.min
