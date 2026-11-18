"""Map :class:`~velbusaio.command_effects.CommandEffect` to Signum Manager REST calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from velbusaio.command_effects import (
    CommandEffect,
    CoverMove,
    CoverPosition,
    PressButton,
    RestoreBrightness,
    SelectProgram,
    SetBrightness,
    SetCurrentTemperature,
    SetLed,
    SetRelay,
    TempSetHvac,
    ThermostatSetMode,
)

if TYPE_CHECKING:
    from velbusaio.bus.manager.backend import ManagerBackend
    from velbusaio.bus.manager.client import ManagerClient
    from velbusaio.controller import Velbus


_LED_SIGNUM = {
    "on": "On",
    "off": "Off",
    "slow": "Slow",
    "fast": "Fast",
    "very_fast": "VeryFast",
}

_THERMOSTAT_ACTION = {
    "comfort": "SwitchToComfortMode",
    "day": "SwitchToDayMode",
    "night": "SwitchToNightMode",
    "safe": "SwitchToSafeMode",
}

_COVER_ACTION = {
    "open": "Open",
    "close": "Close",
    "stop": "Stop",
}


@dataclass
class ManagerSendContext:
    """Signum-specific resolution and state for outbound command effects."""

    backend: ManagerBackend
    last_brightness: dict[tuple[int, int], int] = field(default_factory=dict)

    @property
    def client(self) -> ManagerClient:
        """Return the Signum Manager HTTP/WebSocket client."""
        return self.backend.client

    @property
    def controller(self) -> Velbus:
        """Return the Velbus controller owning this backend."""
        return self.backend.controller

    def thing_id_for(self, address: int, channel: int) -> str | None:
        """Resolve a Signum thing id for a module channel."""
        return self.backend.thing_id_for(address, channel)

    def module_thing_id(self, address: int) -> str | None:
        """Resolve the Signum thing id for a Velbus module address."""
        return self.backend.module_thing_id(address)


async def _invoke_channel(
    ctx: ManagerSendContext,
    address: int,
    channel: int,
    action: str,
    inputs: dict[str, object] | None = None,
) -> None:
    thing_id = ctx.thing_id_for(address, channel)
    if thing_id is None:
        return
    await ctx.client.invoke_action(thing_id, action, inputs or {})


async def apply_command_effect(
    address: int, effect: CommandEffect, ctx: ManagerSendContext
) -> None:
    """Execute a transport-neutral command effect on the Signum Manager API."""
    if isinstance(effect, PressButton):
        await _invoke_channel(ctx, address, effect.channel, "Press")
        return

    if isinstance(effect, SetRelay):
        await _invoke_channel(
            ctx, address, effect.channel, "On" if effect.on else "Off"
        )
        return

    if isinstance(effect, SetBrightness):
        percent = int(effect.level)
        module = ctx.controller.get_module(address)
        if module is not None:
            ch = module.get_channels().get(effect.channel)
            if ch is not None and hasattr(ch, "slider_scale"):
                percent = int(percent * 100 / ch.slider_scale)
        if percent > 0:
            ctx.last_brightness[(address, effect.channel)] = percent
        inputs: dict[str, object] = {"Brightness": percent}
        if effect.transition_time:
            inputs["DimmerSpeed"] = int(effect.transition_time)
        await _invoke_channel(ctx, address, effect.channel, "Brightness", inputs)
        return

    if isinstance(effect, RestoreBrightness):
        level = ctx.last_brightness.get((address, effect.channel), 100)
        await _invoke_channel(
            ctx,
            address,
            effect.channel,
            "Brightness",
            {"Brightness": level},
        )
        return

    if isinstance(effect, CoverMove):
        action = _COVER_ACTION[effect.motion]
        await _invoke_channel(ctx, address, effect.channel, action)
        return

    if isinstance(effect, CoverPosition):
        await _invoke_channel(
            ctx,
            address,
            effect.channel,
            "Position",
            {"Position": int(effect.position)},
        )
        return

    if isinstance(effect, SetLed):
        thing_id = ctx.thing_id_for(address, effect.channel)
        if thing_id is None:
            return
        value = _LED_SIGNUM[effect.mode]
        await ctx.client.set_property(thing_id, "Led", value)
        return

    if isinstance(effect, SetCurrentTemperature):
        await _invoke_channel(
            ctx,
            address,
            1,
            "CurrentTemperature",
            {"Temperature": effect.temperature},
        )
        return

    if isinstance(effect, ThermostatSetMode):
        action = _THERMOSTAT_ACTION[effect.mode]
        await _invoke_channel(ctx, address, 1, action)
        return

    if isinstance(effect, TempSetHvac):
        action = "HeatingMode" if effect.mode == "heating" else "CoolingMode"
        await _invoke_channel(ctx, address, 1, action)
        return

    if isinstance(effect, SelectProgram):
        thing_id = ctx.module_thing_id(address)
        if thing_id is None:
            return
        await ctx.client.invoke_action(
            thing_id, "SelectProgram", {"Program": int(effect.program)}
        )
        return
