"""Sensor Temperature Request Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xE5


@register(COMMAND_CODE)
class SensorTempRequest(DeclarativeMessage):
    """Sensor Temperature Request Message."""

    _command_code = COMMAND_CODE
