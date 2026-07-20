"""Light Value Request message class.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xAA


@register(COMMAND_CODE)
class LightValueRequest(DeclarativeMessage):
    """Light Value Request message."""

    _command_code = COMMAND_CODE
