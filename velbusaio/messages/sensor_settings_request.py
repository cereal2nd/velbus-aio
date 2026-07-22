"""Sensor Settings Request Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xE7


@register(COMMAND_CODE)
class SensorSettingsRequestMessage(DeclarativeMessage):
    """Sensor Settings Request Message."""

    _command_code = COMMAND_CODE
    _priority = "low"
    _rtr = True
    _data_length = 0
    _generates_data_to_binary = False

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([])
