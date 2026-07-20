"""Start relay timer message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ChannelsField, DeclarativeMessage, Int24Field

COMMAND_CODE = 0x03


@register(COMMAND_CODE)
class StartRelayTimerMessage(DeclarativeMessage):
    """Start relay timer message."""

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 4

    relay_channels = ChannelsField(0)
    delay_time = Int24Field(1)
