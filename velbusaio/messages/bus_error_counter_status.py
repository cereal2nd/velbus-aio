"""Bus Error Counter Status message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage

COMMAND_CODE = 0xDA


@register(COMMAND_CODE)
class BusErrorCounterStatusMessage(DeclarativeMessage):
    """Bus Error Counter Status message."""

    _command_code = COMMAND_CODE
    _data_length = 3

    transmit_error_counter = ByteField(0)
    receive_error_counter = ByteField(1)
    bus_off_counter = ByteField(2)
