"""Temperature and thermostat Velbus channels."""

from __future__ import annotations

import math
from typing import Any

from velbusaio.channels._command import _command_message
from velbusaio.channels.base import Channel
from velbusaio.config import ConfigParameter
from velbusaio.const import DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS
from velbusaio.messages.sensor_temp_request import (
    TEMP_AUTOSEND_DISABLED,
    TEMP_AUTOSEND_INTERVAL_MAX,
    TEMP_AUTOSEND_INTERVAL_MIN,
    TEMP_AUTOSEND_ON_CHANGE,
)
from velbusaio.temp_settings import TemperatureSettings


class Temperature(Channel):
    """A Temperature sensor channel."""

    _cur: float = 0
    _cur_precision: float | None = None
    _max: float | None = None
    _min: float | None = None
    _target = 0
    _cmode: str | None = None
    _cool_mode: str | None = None
    _cstatus: str | None = None
    _thermostat = False
    _sleep_timer = 0

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        if self._thermostat:
            return ["sensor", "climate"]
        return ["sensor"]

    def get_class(self) -> str:
        """Return the device class for this channel."""
        return DEVICE_CLASS_TEMPERATURE

    def get_unit(self) -> str:
        """Return the unit of measurement for this channel."""
        return TEMP_CELSIUS

    def get_state(self) -> float:
        """Return the current state of the temperature sensor."""
        return round(float(self._cur), 2)

    def get_sensor_types(self) -> list[str]:
        """Return the temperature sensor key."""
        return ["temperature"]

    def is_temperature(self) -> bool:
        """Return if this channel is a temperature sensor."""
        return True

    def get_max(self) -> float | None:
        """Return the maximum temperature recorded."""
        if self._max is None:
            return None
        return round(self._max, 2)

    def get_min(self) -> float | None:
        """Return the minimum temperature recorded."""
        if self._min is None:
            return None
        return round(self._min, 2)

    def get_climate_target(self) -> float:
        """Return the target temperature."""
        return round(self._target, 2)

    def get_climate_preset(self) -> str | None:
        """Return the climate preset."""
        return self._cmode

    def get_climate_mode(self) -> str | None:
        """Return the climate mode."""
        return self._cstatus

    def get_cool_mode(self) -> str | None:
        """Return the cool mode."""
        return self._cool_mode

    async def set_temp(self, temp: float) -> None:
        """Set the target temperature."""
        msg = _command_message(0xE4, self._module, self._address)
        setattr(msg, "temp", temp)
        await self._writer(msg)

    async def set_temperature_autosend(
        self, mode: str, seconds: int | None = None
    ) -> None:
        """Configure how often the module sends its temperature on the bus.

        :param mode: one of ``"never"`` (auto send disabled),
            ``"on_change"`` (auto send on every temperature change) or
            ``"interval"`` (a fixed interval, requires ``seconds``).
        :param seconds: the interval in seconds (10..255), only used and
            required when ``mode`` is ``"interval"``.
        """
        if mode == "never":
            interval = TEMP_AUTOSEND_DISABLED
        elif mode == "on_change":
            interval = TEMP_AUTOSEND_ON_CHANGE
        elif mode == "interval":
            if seconds is None:
                raise ValueError("seconds is required when mode is 'interval'")
            if not TEMP_AUTOSEND_INTERVAL_MIN <= seconds <= TEMP_AUTOSEND_INTERVAL_MAX:
                raise ValueError(
                    "seconds must be between "
                    f"{TEMP_AUTOSEND_INTERVAL_MIN} and {TEMP_AUTOSEND_INTERVAL_MAX}"
                )
            interval = seconds
        else:
            raise ValueError(
                f"Unknown temperature autosend mode: {mode!r} "
                "(expected 'never', 'on_change' or 'interval')"
            )
        msg = _command_message(0xE5, self._module, self._address, interval)
        await self._writer(msg)

    def get_temp_settings(self) -> TemperatureSettings | None:
        """Return the module temperature settings helper, if available."""
        return self._module.get_temp_settings()

    async def refresh_temp_settings(self, *, force: bool = True) -> dict[str, Any]:
        """Request and cache temperature settings from the module."""
        settings = self.get_temp_settings()
        if settings is None:
            raise RuntimeError(
                f"Channel {self._num} does not support temperature settings"
            )
        return await settings.refresh(force=force)

    async def get_temp_setting(self, key: str) -> Any:
        """Return one temperature setting value (loading from the bus if needed)."""
        settings = self.get_temp_settings()
        if settings is None:
            raise RuntimeError(
                f"Channel {self._num} does not support temperature settings"
            )
        await settings.ensure_loaded()
        return settings.get(key)

    async def set_temp_setting(self, key: str, value: Any) -> None:
        """Write one temperature setting via TempSensorSettings Part1-4."""
        settings = self.get_temp_settings()
        if settings is None:
            raise RuntimeError(
                f"Channel {self._num} does not support temperature settings"
            )
        await settings.set_value(key, value)

    def get_config_parameters(self) -> list[ConfigParameter]:
        """Return discoverable CONFIG parameters for temperature presets."""
        settings = self.get_temp_settings()
        if settings is None:
            return []
        return settings.get_config_parameters()

    async def _switch_mode(self) -> None:
        """Switch the climate mode."""
        if self._cmode == "safe":
            code = 0xDE
        elif self._cmode == "comfort":
            code = 0xDB
        elif self._cmode == "day":
            code = 0xDC
        else:  # "night"
            code = 0xDD

        if self._cstatus == "run":
            sleep = 0x0
        elif self._cstatus == "manual":
            sleep = 0xFFFF
        elif self._cstatus == "sleep":
            sleep = self._sleep_timer
        else:
            sleep = 0x0
        msg = _command_message(code, self._module, self._address, sleep)
        await self._writer(msg)

    async def set_preset(self, preset: str) -> None:
        """Set the climate preset."""
        self._cmode = preset
        await self._switch_mode()

    async def set_climate_mode(self, mode: str) -> None:
        """Set the climate mode."""
        self._cstatus = mode
        await self._switch_mode()

    async def set_mode(self, mode: str) -> None:
        """Set the heat/cool mode."""
        code = 0xDF if mode == "cool" else 0xE0  # 0xE0 = heat
        msg = _command_message(code, self._module, self._address)
        await self._writer(msg)

    async def maybe_update_temperature(self, new_temp: float, precision: float) -> None:
        """Update the temperature only if the new value is different enough."""
        # Based on experiments, Velbus modules seem to truncate (i.e. round down)
        current_temp_rounded_to_precision = (
            math.floor(self._cur / precision) * precision
        )

        if current_temp_rounded_to_precision == new_temp:
            # The newly received temperature is still in line with our current value,
            # but with reduced precision.
            # Don't update (would lose high precision)
            return

        if (
            current_temp_rounded_to_precision - precision
            <= new_temp
            < current_temp_rounded_to_precision
            and self._cur_precision is not None
            and self._cur_precision < precision
        ):
            # The newly received temperature is 1 LSb below the current value
            # and the current value was set by a better precision message
            # Modify the received temperature by "adding precision", while still keeping the same low precision value
            # e.g. (decimal digits represent precision)
            # | Actual  | Msg     | Stored  |
            # | 21.0000 | 21.0000 | 21.0000 |
            # | 20.9375 | 20.5    | 20.9375 |
            new_temp = current_temp_rounded_to_precision - self._cur_precision

        await self.update(
            {
                "cur": new_temp,
                "cur_precision": precision,
            }
        )
