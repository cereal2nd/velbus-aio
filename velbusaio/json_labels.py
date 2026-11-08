"""Stable string labels for Velbus status fields in JSON and integrations."""

from __future__ import annotations

from enum import StrEnum


class BlindDirectionLabel(StrEnum):
    """Blind movement direction in status frames."""

    OFF = "off"
    UP = "up"
    DOWN = "down"


BLIND_STATUS_JSON_MAP: dict[int, BlindDirectionLabel] = {
    0: BlindDirectionLabel.OFF,
    1: BlindDirectionLabel.UP,
    2: BlindDirectionLabel.DOWN,
}


class ThermostatRunStatusLabel(StrEnum):
    """Thermostat run / operating status (lower status bits)."""

    RUN = "run"
    MANUAL = "manual"
    SLEEP = "sleep"
    DISABLE = "disable"


class ThermostatModeLabel(StrEnum):
    """Thermostat comfort mode (upper mode bits)."""

    SAFE = "safe"
    NIGHT = "night"
    DAY = "day"
    COMFORT = "comfort"


THERMOSTAT_STATUS_JSON_MAP: dict[int, ThermostatRunStatusLabel] = {
    0: ThermostatRunStatusLabel.RUN,
    2: ThermostatRunStatusLabel.MANUAL,
    4: ThermostatRunStatusLabel.SLEEP,
    6: ThermostatRunStatusLabel.DISABLE,
}

THERMOSTAT_MODE_JSON_MAP: dict[int, ThermostatModeLabel] = {
    0: ThermostatModeLabel.SAFE,
    16: ThermostatModeLabel.NIGHT,
    32: ThermostatModeLabel.DAY,
    64: ThermostatModeLabel.COMFORT,
}
