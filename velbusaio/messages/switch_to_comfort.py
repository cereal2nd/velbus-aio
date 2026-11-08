"""Switch to comfort message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.messages.switch_to_mode import SwitchToModeMessage

COMMAND_CODE = 0xDB


@register(COMMAND_CODE)
class SwitchToComfortMessage(SwitchToModeMessage):
    """Switch to comfort message."""

    _command_code = COMMAND_CODE
    __init__ = SwitchToModeMessage.__init__
