"""TempSensorSettingsPart4 message implementation.

:author: Danny De Gaspari
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xB9


@register(COMMAND_CODE)
class TempSensorSettingsPart4(DeclarativeMessage):
    """TempSensorSettingsPart4 message class."""

    _command_code = COMMAND_CODE
