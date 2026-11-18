"""Transport-neutral descriptions of outbound Velbus command semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LedMode = Literal["on", "off", "slow", "fast", "very_fast"]
ThermostatMode = Literal["comfort", "day", "night", "safe"]
CoverMotion = Literal["open", "close", "stop"]
HvacMode = Literal["heating", "cooling"]


def first_channel(channels: object) -> int | None:
    """Return the first channel from a Velbus channel field value."""
    if not channels:
        return None
    if isinstance(channels, list):
        if not channels:
            return None
        return int(channels[0])
    if isinstance(channels, int):
        return channels
    return None


@dataclass(frozen=True)
class PressButton:
    """Short press on a push-button channel."""

    channel: int


@dataclass(frozen=True)
class SetRelay:
    """Turn a relay channel on or off."""

    channel: int
    on: bool


@dataclass(frozen=True)
class SetBrightness:
    """Set dimmer level on a channel."""

    channel: int
    level: int
    transition_time: int | None = None


@dataclass(frozen=True)
class RestoreBrightness:
    """Restore the previous dimmer level on a channel."""

    channel: int


@dataclass(frozen=True)
class CoverMove:
    """Move a cover up, down, or stop."""

    channel: int
    motion: CoverMotion


@dataclass(frozen=True)
class CoverPosition:
    """Set cover position as a percentage."""

    channel: int
    position: int


@dataclass(frozen=True)
class SetLed:
    """Set button LED indication on a channel."""

    channel: int
    mode: LedMode


@dataclass(frozen=True)
class SetCurrentTemperature:
    """Set the thermostat current temperature."""

    temperature: float


@dataclass(frozen=True)
class ThermostatSetMode:
    """Switch thermostat comfort/day/night/safe mode."""

    mode: ThermostatMode


@dataclass(frozen=True)
class TempSetHvac:
    """Set heating or cooling HVAC mode."""

    mode: HvacMode


@dataclass(frozen=True)
class SelectProgram:
    """Select a program on a module."""

    program: int


CommandEffect = (
    PressButton
    | SetRelay
    | SetBrightness
    | RestoreBrightness
    | CoverMove
    | CoverPosition
    | SetLed
    | SetCurrentTemperature
    | ThermostatSetMode
    | TempSetHvac
    | SelectProgram
)


def relay_command_effect(channels: object, on: bool) -> SetRelay | None:
    """Build a :class:`SetRelay` effect from a relay channel field."""
    channel = first_channel(channels)
    if channel is None:
        return None
    return SetRelay(channel=channel, on=on)


def led_command_effect(leds: object, mode: LedMode) -> SetLed | None:
    """Build a :class:`SetLed` effect from an LED channel field."""
    channel = first_channel(leds)
    if channel is None:
        return None
    return SetLed(channel=channel, mode=mode)
