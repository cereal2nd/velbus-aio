"""Dimmer (light) Velbus channels."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from velbusaio.channels._command import _command_message
from velbusaio.channels.base import Channel
from velbusaio.message import Message

if TYPE_CHECKING:
    from velbusaio.module import Module


class Dimmer(Channel):
    """A Dimmer channel."""

    _state: int = 0

    def __init__(
        self,
        module: Module,
        num: int,
        name: str,
        nameEditable: bool,
        subDevice: bool,
        writer: Callable[[Message], Awaitable[None]],
        address: int,
        slider_scale: int = 100,
    ) -> None:
        """Initialize the dimmer channel."""
        super().__init__(module, num, name, nameEditable, subDevice, writer, address)

        self.slider_scale = slider_scale
        # VMB4DC has dim values 0(off), 1-99(dimmed), 100(full on)
        # VMBDALI has dim values 0(off), 1-253(dimmed), 254(full on), 255(previous value)

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        return ["light"]

    def is_on(self) -> bool:
        """Check if a dimmer is turned on."""
        return self._state != 0

    def get_dimmer_state(self) -> int:
        """Return the dimmer state."""
        return int(self._state * 100 / self.slider_scale)

    async def set_dimmer_state(self, slider: int, transitiontime: int = 0) -> None:
        """Set dimmer to slider."""
        msg = _command_message(0x07, self._module, self._address)
        setattr(msg, "dimmer_state", int(slider * self.slider_scale / 100))
        setattr(msg, "dimmer_transitiontime", int(transitiontime))
        setattr(msg, "dimmer_channels", [self._num])
        await self._writer(msg)

    async def restore_dimmer_state(self, transitiontime: int = 0) -> None:
        """Restore dimmer to last known state."""
        msg = _command_message(0x11, self._module, self._address)
        if self.slider_scale == 254 and transitiontime == 0:
            # New dimmers treat the trailing bytes as fade mode / unchanged (0x00, 0xFF).
            transitiontime = 0x00FF
        setattr(msg, "dimmer_transitiontime", int(transitiontime))
        setattr(msg, "dimmer_channels", [self._num])
        await self._writer(msg)
