"""Cover (blind) Velbus channels."""

from __future__ import annotations

import velbusaio.channels as _channels_pkg
from velbusaio.channels._command import _command_message
from velbusaio.channels.base import Channel


class Blind(Channel):
    """A blind channel."""

    _state: int | None = None
    # State reports the direction of *movement*: moving up, moving down or stopped
    _position: int | None = None
    # Position reporting is not supported by VMBxBL modules (only in BLE/BLS)

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        return ["cover"]

    def get_position(self) -> int | None:
        """Return the blind position."""
        return self._position

    def get_state(self) -> int | None:
        """Return the blind state."""
        return self._state

    def is_opening(self) -> bool:
        """Return if the blind is opening."""
        return self._state == 0x01

    def is_closing(self) -> bool:
        """Return if the blind is closing."""
        return self._state == 0x02

    def is_stopped(self) -> bool:
        """Return if the blind is stopped."""
        return self._state == 0x00

    def is_closed(self) -> bool | None:
        """Report if the blind is fully closed."""
        if self._position is None:
            return None
        return self._position == 100

    def is_open(self) -> bool | None:
        """Report if the blind is fully open."""
        if self._position is None:
            return None
        return self._position == 0

    def support_position(self) -> bool:
        """Return if the blind supports position get/set (module command 0x1C)."""
        return _channels_pkg.commandRegistry.has_command(0x1C, self._module.get_type())

    async def open(self) -> None:
        """Open the blind."""
        msg = _command_message(0x05, self._module, self._address)
        setattr(msg, "channel", self._num)
        await self._writer(msg)

    async def close(self) -> None:
        """Close the blind."""
        msg = _command_message(0x06, self._module, self._address)
        setattr(msg, "channel", self._num)
        await self._writer(msg)

    async def stop(self) -> None:
        """Stop the blind."""
        msg = _command_message(0x04, self._module, self._address)
        setattr(msg, "channel", self._num)
        await self._writer(msg)

    async def set_position(self, position: int) -> None:
        """Set the blind to a specific position."""
        # may not be supported by the module
        if position == 100:
            # at least VMB1BLS ignores command 0x1C with position 0x64
            await self.close()
            return
        msg = _command_message(0x1C, self._module, self._address)
        setattr(msg, "channel", self._num)
        setattr(msg, "position", position)
        await self._writer(msg)
