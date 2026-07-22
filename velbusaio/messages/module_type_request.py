"""Module Type Request Message class.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.message_fields import DeclarativeMessage


class ModuleTypeRequestMessage(DeclarativeMessage):
    """Module Type Request Message."""

    _priority = "low"
    _rtr = True
    _data_length = 0
    _generates_data_to_binary = False

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([])
