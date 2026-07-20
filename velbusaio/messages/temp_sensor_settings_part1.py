"""TempSensorSettingsPart1 message class.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xE8


@register(COMMAND_CODE)
class TempSensorSettingsPart1(DeclarativeMessage):
    """TempSensorSettingsPart1 message class."""

    _command_code = COMMAND_CODE
