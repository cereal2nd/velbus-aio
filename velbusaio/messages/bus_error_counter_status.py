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

    def populate(self, priority, address, rtr, data):
        """Populate message fields without updating address attributes."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 3)
        self.transmit_error_counter = data[0]
        self.receive_error_counter = data[1]
        self.bus_off_counter = data[2]
