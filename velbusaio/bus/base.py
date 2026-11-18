"""Shared transport contract for Velbus controller backends."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import datetime
from typing import Protocol

from velbusaio.message import Message

AuthFailedCallback = Callable[[], Awaitable[None] | None]


class VelbusBusBackend(Protocol):
    """Lifecycle surface shared by manager and raw bus backends."""

    @property
    def is_connected(self) -> bool:
        """Return whether the bus link is usable for I/O."""

    async def connect(self) -> None:
        """Open the transport."""

    async def start(self) -> None:
        """Load modules after connect."""

    async def stop(self) -> None:
        """Shut down transport I/O."""

    async def scan(self) -> None:
        """Rescan or refresh the installation."""

    async def send(self, msg: Message) -> None:
        """Send a Velbus message."""

    async def sync_clock(self, dt: datetime.datetime | None = None) -> None:
        """Synchronize module clocks when supported."""

    def schedule_reconnect(self) -> None:
        """Start auto-reconnect when the link drops."""

    async def wait_on_all_messages_sent_async(self) -> None:
        """Wait until the outbound queue is drained."""

    def add_auth_failed_callback(self, meth: AuthFailedCallback) -> None:
        """Register a coroutine when Signum Manager rejects the access token."""

    def remove_auth_failed_callback(self, meth: AuthFailedCallback) -> None:
        """Remove a previously registered auth-failed callback."""
