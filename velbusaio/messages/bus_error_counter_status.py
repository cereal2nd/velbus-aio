"""Bus Error Counter Status message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import FieldSpec, Message

COMMAND_CODE = 0xDA


@register(COMMAND_CODE)
class BusErrorCounterStatusMessage(Message):
    """Bus Error Counter Status message."""

    command_code = COMMAND_CODE
    fields = [
        FieldSpec("transmit_error_counter", "B"),
        FieldSpec("receive_error_counter", "B"),
        FieldSpec("bus_off_counter", "B"),
    ]

    validators = [
        lambda self: self.needs_low_priority(self.priority),
        lambda self: self.needs_no_rtr(self.rtr),
    ]

    def __init__(self, address=None):
        """Initialize Bus Error Counter Status message."""
        super().__init__()
        self.transmit_error_counter = 0
        self.receive_error_counter = 0
        self.bus_off_counter = 0
        self.set_defaults(address)
