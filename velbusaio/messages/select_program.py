"""Select Program Message.

:author: Danny De Gaspari
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import BitField, DeclarativeMessage

COMMAND_CODE = 0xB3


@register(COMMAND_CODE)
class SelectProgramMessage(DeclarativeMessage):
    """Select Program Message."""

    _command_code = COMMAND_CODE
    _data_length = 1

    select_program = BitField(0, 0x03, default=0, serializable=True)

    def __init__(self, address=None, program=0):
        """Initialize Select Program Message Object."""
        super().__init__(address)
        self.select_program = program
