"""TempSensorSettingsPart3 message implementation.

:author: Danny De Gaspari
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xC6


@register(COMMAND_CODE)
class TempSensorSettingsPart3(DeclarativeMessage):
    """TempSensorSettingsPart3 message class."""

    _command_code = COMMAND_CODE
