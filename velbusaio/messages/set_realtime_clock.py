"""Set realtime Clock Message.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage

COMMAND_CODE = 0xD8


@register(COMMAND_CODE)
class SetRealtimeClock(DeclarativeMessage):
    """Set realtime Clock Message."""

    _command_code = COMMAND_CODE
    _data_length = 3

    _wday = ByteField(0, default=None)
    _hour = ByteField(1, default=None)
    _min = ByteField(2, default=None)

    def __init__(self, address=0x00, wday=None, hour=None, min=None) -> None:
        """Initialize Set realtime Clock Message Object."""
        super().__init__(address)
        if wday is not None:
            self._wday = wday
        if hour is not None:
            self._hour = hour
        if min is not None:
            self._min = min
