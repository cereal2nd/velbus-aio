"""TempSensorSettingsPart2 message implementation.

:author: Danny De Gaspari
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xE9


@register(COMMAND_CODE)
class TempSensorSettingsPart2(DeclarativeMessage):
    """TempSensorSettingsPart2 message class."""

    _command_code = COMMAND_CODE
