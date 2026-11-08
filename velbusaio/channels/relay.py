"""Relay (switch) Velbus channels."""

from __future__ import annotations

import velbusaio.channels as _channels_pkg
from velbusaio.channels._command import _command_message
from velbusaio.channels.base import Channel
from velbusaio.config import ConfigParameter


class Relay(Channel):
    """A Relay channel."""

    _on: bool | None = None
    _enabled = True
    _inhibit = False
    _forced_on = False
    _forced_off = False
    _disabled = False

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        if self._enabled:
            return ["switch"]
        return []

    def is_on(self) -> bool | None:
        """Return if this relay is on."""
        return self._on

    def is_inhibit(self) -> bool:
        """Return if this relay is inhibited."""
        return self._inhibit

    def is_forced_on(self) -> bool:
        """Return if this relay is forced on."""
        return self._forced_on

    def is_forced_off(self) -> bool:
        """Return if this relay is forced off."""
        return self._forced_off

    def is_disabled(self) -> bool:
        """Return if this relay is disabled."""
        return self._disabled

    def supports_inhibit(self) -> bool:
        """Return True when inhibit / cancel-inhibit commands are available."""
        return _channels_pkg.commandRegistry.has_command(0x16, self._module.get_type())

    def supports_forced_on(self) -> bool:
        """Return True when forced-on / cancel-forced-on commands are available."""
        return _channels_pkg.commandRegistry.has_command(0x14, self._module.get_type())

    def supports_forced_off(self) -> bool:
        """Return True when forced-off / cancel-forced-off commands are available."""
        return _channels_pkg.commandRegistry.has_command(0x12, self._module.get_type())

    async def turn_on(self) -> None:
        """Send the turn on message."""
        msg = _command_message(0x02, self._module, self._address)
        setattr(msg, "relay_channels", [self._num])
        await self._writer(msg)

    async def turn_off(self) -> None:
        """Send the turn off message."""
        msg = _command_message(0x01, self._module, self._address)
        setattr(msg, "relay_channels", [self._num])
        await self._writer(msg)

    async def set_forced_on(self, state: bool) -> None:
        """Set or cancel forced on."""
        code = 0x14 if state else 0x15
        msg = _command_message(code, self._module, self._address)
        setattr(msg, "channel", self._num)
        if state:
            setattr(msg, "delay_time", 0xFFFFFF)  # Permanent
        await self._writer(msg)

    async def set_forced_off(self, state: bool) -> None:
        """Set or cancel forced off."""
        code = 0x12 if state else 0x13
        msg = _command_message(code, self._module, self._address)
        setattr(msg, "channel", self._num)
        if state:
            setattr(msg, "delay_time", 0xFFFFFF)  # Permanent
        await self._writer(msg)

    async def set_inhibit(self, state: bool) -> None:
        """Set or cancel inhibit."""
        code = 0x16 if state else 0x17
        msg = _command_message(code, self._module, self._address)
        setattr(msg, "channel", self._num)
        if state:
            setattr(msg, "delay_time", 0xFFFFFF)  # Permanent
        await self._writer(msg)

    async def set_name_persistent(self, name: str) -> None:
        """Write this channel's name to module EEPROM."""
        await self._module.set_channel_name_persistent(self._num, name)

    async def get_normal_closed(self, *, refresh: bool = False) -> bool | None:
        """Return True when this relay is programmed as normally closed."""
        table = self.get_action_table()
        if table is None:
            return None
        return await table.get_normal_closed(refresh=refresh)

    async def set_normal_closed(self, normal_closed: bool) -> None:
        """Program NO/NC contact behaviour in EEPROM."""
        table = self.get_action_table()
        if table is None:
            raise RuntimeError(f"Channel {self._num} has no action table")
        await table.set_normal_closed(normal_closed)

    def get_config_parameters(self) -> list[ConfigParameter]:
        """Return discoverable CONFIG parameters for this relay channel."""
        params: list[ConfigParameter] = [
            ConfigParameter(
                key="name",
                label="Channel name",
                kind="text",
                getter=self._get_name_value,
                setter=self.set_name_persistent,
                max_length=16,
                channel=self._num,
                entity=False,
            ),
        ]
        if self.supports_inhibit():
            params.append(
                ConfigParameter(
                    key="inhibit",
                    label="Inhibit",
                    kind="bool",
                    getter=self._get_inhibit_value,
                    setter=self.set_inhibit,
                    channel=self._num,
                )
            )
        if self.supports_forced_on():
            params.append(
                ConfigParameter(
                    key="forced_on",
                    label="Forced on",
                    kind="bool",
                    getter=self._get_forced_on_value,
                    setter=self.set_forced_on,
                    channel=self._num,
                )
            )
        if self.supports_forced_off():
            params.append(
                ConfigParameter(
                    key="forced_off",
                    label="Forced off",
                    kind="bool",
                    getter=self._get_forced_off_value,
                    setter=self.set_forced_off,
                    channel=self._num,
                )
            )
        table = self.get_action_table()
        if table is not None and table.noc_address is not None:
            params.append(
                ConfigParameter(
                    key="contact",
                    label="Contact",
                    kind="select",
                    getter=self._get_contact_value,
                    setter=self._set_contact_value,
                    options=["NO", "NC"],
                    channel=self._num,
                    entity=False,
                )
            )
        return params

    async def _get_name_value(self) -> str:
        return self.get_name()

    async def _get_inhibit_value(self) -> bool:
        return self.is_inhibit()

    async def _get_forced_on_value(self) -> bool:
        return self.is_forced_on()

    async def _get_forced_off_value(self) -> bool:
        return self.is_forced_off()

    async def _get_contact_value(self) -> str:
        normal_closed = await self.get_normal_closed()
        if normal_closed is None:
            return "NO"
        return "NC" if normal_closed else "NO"

    async def _set_contact_value(self, value: str) -> None:
        await self.set_normal_closed(str(value).upper() == "NC")
