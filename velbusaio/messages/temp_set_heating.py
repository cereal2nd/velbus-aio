"""Temp Set Heating Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage

COMMAND_CODE = 0xE0


@register(COMMAND_CODE)
class TempSetHeatingMessage(DeclarativeMessage):
    """Set Heating Temperature Message."""

    _command_code = COMMAND_CODE
    _priority = None

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, 0xAA])
