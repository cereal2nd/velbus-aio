"""Dali Device Settings Request message.

:author: Niels Laukens
"""

from __future__ import annotations

import enum

from velbusaio.command_registry import register
from velbusaio.message_fields import DeclarativeMessage
from velbusaio.messages.dali_device_settings import DaliDeviceSetting

COMMAND_CODE = 0xE7


class DataSource(enum.Enum):
    """Data source enum."""

    FromMemory = 0
    FromDaliDevice = 1


@register(COMMAND_CODE)
class DaliDeviceSettingsRequest(DeclarativeMessage):
    """Dali Device Settings Request message."""

    _command_code = COMMAND_CODE
    _data_length = 2

    def __init__(self, address: int | None = None):
        """Initialize Dali Device Settings Request message."""
        super().__init__(address)
        self.channel: int | None = None
        self.data_source: DataSource | None = None
        self.settings: DaliDeviceSetting | int | None = None

    def populate(self, priority: int, address: int, rtr: bool, data: bytes) -> None:
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
        assert self.channel is not None
        data = bytearray([COMMAND_CODE, self.channel, DataSource.FromMemory.value])
        if isinstance(self.settings, DaliDeviceSetting):
            data.append(self.settings.value)
        elif self.settings is not None:
            data.append(self.settings)
        return bytes(data)
