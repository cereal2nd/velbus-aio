"""Translate velbus bus messages into Signum Manager REST calls."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from velbusaio.bus.manager.effects import ManagerSendContext, apply_command_effect
from velbusaio.message import Message
from velbusaio.messages.channel_name_request import ChannelNameRequestMessage
from velbusaio.messages.counter_status_request import CounterStatusRequestMessage
from velbusaio.messages.memo_text import MemoTextMessage
from velbusaio.messages.module_status_request import ModuleStatusRequestMessage
from velbusaio.messages.module_type_request import ModuleTypeRequestMessage
from velbusaio.messages.read_data_block_from_memory import (
    ReadDataBlockFromMemoryMessage,
)
from velbusaio.messages.read_data_from_memory import ReadDataFromMemoryMessage
from velbusaio.messages.set_date import SetDate
from velbusaio.messages.set_daylight_saving import SetDaylightSaving
from velbusaio.messages.set_realtime_clock import SetRealtimeClock

if TYPE_CHECKING:
    from velbusaio.bus.manager.backend import ManagerBackend

_LOGGER = logging.getLogger(__name__)

_BUS_ONLY: tuple[type[Message], ...] = (
    ModuleStatusRequestMessage,
    ModuleTypeRequestMessage,
    ReadDataFromMemoryMessage,
    ReadDataBlockFromMemoryMessage,
    ChannelNameRequestMessage,
    CounterStatusRequestMessage,
    SetDate,
    SetRealtimeClock,
    SetDaylightSaving,
    MemoTextMessage,
)


class ManagerCommandTranslator:
    """Maps outbound :class:`~velbusaio.message.Message` objects to Signum actions."""

    def __init__(self, backend: ManagerBackend) -> None:
        """Wire the translator to a :class:`~velbusaio.bus.manager.backend.ManagerBackend`."""
        self._backend = backend
        self._last_brightness: dict[tuple[int, int], int] = {}
        self._ctx = ManagerSendContext(
            backend=backend, last_brightness=self._last_brightness
        )

    def remember_brightness(self, address: int, channel: int, percent: int) -> None:
        """Track the last non-zero dimmer level for restore-brightness actions."""
        if percent > 0:
            self._last_brightness[(address, channel)] = percent

    async def send(self, msg: Message) -> None:
        """Send a Velbus message through the Signum Manager API."""
        if isinstance(msg, _BUS_ONLY):
            return

        effect_factory = getattr(msg, "command_effect", None)
        if effect_factory is None:
            _LOGGER.debug(
                "Dropped unsupported Signum translation for %s", type(msg).__name__
            )
            return

        effect = effect_factory()
        if effect is None:
            return

        await apply_command_effect(msg.address, effect, self._ctx)
