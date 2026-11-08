"""Switch to night message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.messages.switch_to_mode import SwitchToModeMessage

COMMAND_CODE = 0xDD


@register(COMMAND_CODE)
class SwitchToNightMessage(SwitchToModeMessage):
    """Switch to night message."""

    _command_code = COMMAND_CODE
    __init__ = SwitchToModeMessage.__init__
