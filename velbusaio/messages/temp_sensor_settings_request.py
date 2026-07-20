"""TempSensorSettingsRequest message implementation.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xE7


@register(COMMAND_CODE)
class TempSensorSettingsRequest(DeclarativeMessage):
    """TempSensorSettingsRequest message class."""

    _command_code = COMMAND_CODE
