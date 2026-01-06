"""Dali Device Settings Request message.

:author: Niels Laukens
"""

from __future__ import annotations

import enum

from velbusaio.command_registry import register
from velbusaio.message import Message
from velbusaio.messages.dali_device_settings import DaliDeviceSetting

COMMAND_CODE = 0xE7


class DataSource(enum.Enum):
    """Data source enum."""

    FromMemory = 0
    FromDaliDevice = 1


@register(COMMAND_CODE, ["VMBDALI", "VMBDALI-20"])
class DaliDeviceSettingsRequest(Message):
    """Dali Device Settings Request message."""

    def __init__(self, address: int | None = None):
        """Initialize Dali Device Settings Request message."""
        super().__init__()
        self.channel: int = None
        self.data_source: DataSource = None
        self.settings: DaliDeviceSetting = None
        self.set_defaults(address)

    def populate(self, priority, address: int, rtr: int, data: bytes) -> None:
        """Populate message attributes."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 2)
        self.set_attributes(priority, address, rtr)
        self.channel = data[0]
        self.data_source = DataSource(data[1])
        if len(data) >= 3:
            self.settings = data[2]
        else:
            self.settings = None  # all

    def data_to_binary(self) -> bytes:
        """Generate binary data for the message."""
        data = bytearray([COMMAND_CODE, self.channel, DataSource.FromMemory.value])
        if self.settings is not None:
            data.append(self.settings.value)
        return bytes(data)
