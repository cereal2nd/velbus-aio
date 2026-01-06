"""IR Receiver Status message class.

:author: David Danssaert <david.danssaert@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.messages.module_status import ModuleStatusMessage

COMMAND_CODE = 0xEB


@register(COMMAND_CODE, ["VMB8IR"])
class IRReceiverStatusMessage(ModuleStatusMessage):
    """IR Receiver Status message."""
