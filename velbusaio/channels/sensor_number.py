"""Numeric sensor Velbus channels."""

from __future__ import annotations

from velbusaio.channels.base import Channel


class SensorNumber(Channel):
    """A Numeric Sensor channel."""

    _cur: float = 0
    _unit: str | None = None
    _sensor_type: str | None = None

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        return ["sensor"]

    def get_class(self) -> None:
        """Return the device class for this channel."""
        return

    def get_unit(self) -> str | None:
        """Return the unit of measurement for this channel."""
        return self._unit

    def get_state(self) -> float:
        """Return the current state of the temperature sensor."""
        return round(self._cur, 2)

    def get_sensor_type(self) -> str | None:
        """Return the sensor type."""
        return self._sensor_type
