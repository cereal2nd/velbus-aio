"""Shared thermostat mode-switch message (sleep timer + command code).

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.message_fields import DeclarativeMessage, Int16Field


class _SleepInt16Field(Int16Field):
    """Sleep timer on outbound mode switches; inbound populate may have no payload."""

    def parse(self, data: bytes) -> int:
        assert self.byte_index is not None
        if self.byte_index + 2 > len(data):
            return self.default if self.default is not None else 0
        return super().parse(data)


class SwitchToModeMessage(DeclarativeMessage):
    """Thermostat mode switch; subclasses set ``_command_code`` only."""

    _priority = None

    sleep = _SleepInt16Field(0)

    def __init__(self, address: int | None = None, sleep: int = 0) -> None:
        """Initialize with optional module address and sleep timer (seconds)."""
        super().__init__(address)
        self.sleep = sleep
