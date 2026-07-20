"""Set Daylight Saving Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage

COMMAND_CODE = 0xAF


@register(COMMAND_CODE)
class SetDaylightSaving(DeclarativeMessage):
    """Set Daylight Saving Message."""

    _command_code = COMMAND_CODE
    _data_length = 1

    _ds = ByteField(0, default=None)

    def __init__(self, address=0x00, ds=None) -> None:
        """Initialize Set Daylight Saving Message Object."""
        super().__init__(address)
        if ds is not None:
            self._ds = ds
