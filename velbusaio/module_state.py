"""Shared typing base for :class:`velbusaio.module.Module` mixins."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import TYPE_CHECKING, Any

from velbusaio.channels import Channel
from velbusaio.memory import MemoryBackend
from velbusaio.message import Message
from velbusaio.properties import Property
from velbusaio.temp_settings import TemperatureSettings

if TYPE_CHECKING:
    from velbusaio.module import Module


class ModuleMixinState:
    """Attributes and hooks provided by :class:`~velbusaio.module.Module` for mixins."""

    _address: int
    _type: int
    _data: dict[str, Any]
    _name: str | dict[Any, Any] | None
    _name_buffer: dict[int, str]
    _sub_address: dict[int, int]
    _cache_dir: str | None
    _is_loading: bool
    _got_status: asyncio.Event
    _channels: dict[int, Channel]
    _properties: dict[str, Property]
    _memory: MemoryBackend | None
    _temp_settings: TemperatureSettings | None
    loaded: bool
    _use_cache: bool
    _loaded_cache: dict[str, Any]
    _cache_lock: asyncio.Lock
    _on_module_found: Callable[[Module], Awaitable[None]] | None
    _writer: Callable[[Message], Awaitable[None]]
    _log: logging.Logger
    _message_handlers: dict[type[Message], Callable[..., Awaitable[None]]]

    def get_type(self) -> int:
        """Implemented on :class:`~velbusaio.module.Module`."""
        raise NotImplementedError

    def get_type_name(self) -> str:
        """Implemented on :class:`~velbusaio.module.Module`."""
        raise NotImplementedError

    def number_of_channels(self) -> int:
        """Implemented on :class:`~velbusaio.module.Module`."""
        raise NotImplementedError

    def calc_channel_offset(self, address: int) -> int:
        """Implemented on :class:`~velbusaio.module.Module`."""
        raise NotImplementedError

    def _translate_channel_name(self, channel: str | int) -> int:
        """Implemented on message-handler / core module mixins."""
        raise NotImplementedError

    def _load(self) -> None:
        """Implemented on :class:`~velbusaio.module.Module`."""
        raise NotImplementedError

    async def _cache(self) -> None:
        """Implemented on :class:`~velbusaio.module_scan.ModuleScanMixin`."""
        raise NotImplementedError

    async def _update_channel(self, channel: int, updates: dict[str, Any]) -> None:
        """Implemented on :class:`~velbusaio.module_handlers.ModuleMessageHandlersMixin`."""
        raise NotImplementedError
