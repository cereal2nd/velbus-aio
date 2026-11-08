"""Sensor Temperature Request Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from typing import cast

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

    def getCurTemp(self) -> float:
        """Get current temperature."""
        return cast("float", self.cur)

    def getMaxTemp(self) -> float:
        """Get maximum temperature."""
        return cast("float", self.max)

    def getMinTemp(self) -> float:
        """Get minimum temperature."""
        return cast("float", self.min)
