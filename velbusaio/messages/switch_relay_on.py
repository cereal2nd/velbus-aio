"""Switch Relay Off Message."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.const import PRIORITY_HIGH
from velbusaio.message import FieldSpec, Message

COMMAND_CODE = 0x02


@register(COMMAND_CODE)
class SwitchRelayOnMessage(Message):
    """Switch Relay On Message."""

    command_code = COMMAND_CODE
    default_priority = PRIORITY_HIGH

    def __init__(self, address=None):
        """Initialize SwitchRelayOnMessage class."""
        super().__init__()
        self.relay_channels = []
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 1)
        self.set_attributes(priority, address, rtr)
        self.relay_channels = self.byte_to_channels(data[0])

    def data_to_binary(self):
        """:return: bytes"""
        return bytes([COMMAND_CODE, self.channels_to_byte(self.relay_channels)])


@register(
    COMMAND_CODE, ["VMB4RYLD-20", "VMB4RYNO-20", "VMB1RYS", "VMB1RYNO", "VMB1RYNOS"]
)
class SwitchRelayOnMessage20(SwitchRelayOnMessage):
    """Switch Relay On Message for -20 series."""

    def data_to_binary(self):
        """:return: bytes"""
        # For these modules, we send the channel index (1-8), not a bitmask
        if self.relay_channels:
            return bytes([COMMAND_CODE, self.relay_channels[0]])
        return bytes([COMMAND_CODE, 0])
