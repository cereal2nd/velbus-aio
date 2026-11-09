"""Button, counter, and thermostat-input Velbus channels."""

from __future__ import annotations

import asyncio

from velbusaio.channels._command import _command_message
from velbusaio.channels.base import Channel
from velbusaio.config import ConfigParameter
from velbusaio.const import (
    ENERGY_KILO_WATT_HOUR,
    VOLUME_CUBIC_METER_HOUR,
    VOLUME_LITERS_HOUR,
)
from velbusaio.exceptions import VelbusConfigError


class Button(Channel):
    """A Button channel."""

    _enabled = True
    _closed = False
    _led_state: str | None = None
    _long = False
    _saved_reaction_time: int | None = None

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        if self._enabled:
            return ["binary_sensor", "led", "button"]
        return []

    def is_enabled(self) -> bool:
        """Return whether this channel is currently enabled."""
        return self._enabled

    def supports_channel_enable(self) -> bool:
        """Return True when EEPROM enable/disable is available."""
        return self._module.get_channel_enable_spec(self._num) is not None

    async def get_channel_enabled(self, *, refresh: bool = False) -> bool | None:
        """Return EEPROM enable state (reaction time != disabled)."""
        spec = self._module.get_channel_enable_spec(self._num)
        if spec is None:
            return None
        memory = self._module.get_memory()
        if memory is None:
            return self._enabled
        if not refresh:
            cached = memory.get_cached(spec["address"])
            if cached is not None:
                enabled = cached != spec["disabled_value"]
                if enabled:
                    self._saved_reaction_time = cached
                self._enabled = enabled
                return enabled
        value = await memory.read_byte(spec["address"], use_cache=not refresh)
        enabled = value != spec["disabled_value"]
        if enabled:
            self._saved_reaction_time = value
        self._enabled = enabled
        return enabled

    async def set_channel_enabled(self, enabled: bool) -> None:
        """Enable or disable this channel via the reaction-time EEPROM byte."""
        spec = self._module.get_channel_enable_spec(self._num)
        if spec is None:
            raise VelbusConfigError(
                f"Channel {self._num} does not support enable/disable"
            )
        memory = self._module.get_memory()
        if memory is None:
            raise RuntimeError("Module memory backend is not initialized")
        current = await memory.read_byte(spec["address"])
        if current != spec["disabled_value"]:
            self._saved_reaction_time = current
        if enabled:
            saved = self._saved_reaction_time
            if saved is not None and saved != spec["disabled_value"]:
                write_value = saved
            else:
                write_value = spec["enabled_value"]
        else:
            write_value = spec["disabled_value"]
        await memory.write_byte(spec["address"], write_value & 0xFF)
        await self.update({"enabled": enabled})

    async def set_name_persistent(self, name: str) -> None:
        """Write this channel's name to module EEPROM."""
        await self._module.set_channel_name_persistent(self._num, name)

    def get_config_parameters(self) -> list[ConfigParameter]:
        """Return discoverable CONFIG parameters for this button channel."""
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
        if self.supports_channel_enable():
            params.append(
                ConfigParameter(
                    key="enabled",
                    label="Enabled",
                    kind="bool",
                    getter=self._get_enabled_value,
                    setter=self.set_channel_enabled,
                    channel=self._num,
                )
            )
        return params

    async def _get_name_value(self) -> str:
        return self.get_name()

    async def _get_enabled_value(self) -> bool:
        enabled = await self.get_channel_enabled()
        return True if enabled is None else enabled

    def is_closed(self) -> bool:
        """Return if this button is on."""
        return self._closed

    def is_long_pressed(self) -> bool:
        """Return if this button is currently long pressed."""
        return self._long

    def is_on(self) -> bool:
        """Return if this relay is on."""
        return self._led_state == "on"

    async def set_led_state(self, state: str) -> None:
        """Set led."""
        if state == "on":
            code = 0xF6
        elif state == "slow":
            code = 0xF7
        elif state == "fast":
            code = 0xF8
        elif state == "off":
            code = 0xF5
        else:
            return

        _mod_add = self.get_module_address("Button")
        _chn_num = self._num - self._module.calc_channel_offset(_mod_add)
        msg = _command_message(code, self._module, _mod_add)
        setattr(msg, "leds", [_chn_num])
        await self._writer(msg)
        await self.update({"led_state": state})

    async def press(self) -> None:
        """Press the button."""
        _mod_add = self.get_module_address("Button")
        _chn_num = self._num - self._module.calc_channel_offset(_mod_add)
        # send the just pressed
        msg = _command_message(0x00, self._module, _mod_add)
        setattr(msg, "closed", [_chn_num])
        await self._writer(msg)
        # wait
        await asyncio.sleep(0.3)
        # send the just released
        msg = _command_message(0x00, self._module, _mod_add)
        setattr(msg, "opened", [_chn_num])
        await self._writer(msg)


class ButtonCounter(Button):
    """A ButtonCounter channel.

    This channel can act as a button and as a counter
    => standard     this is the calculated power value
    => is_counter   this is the numeric energy value
    """

    _Unit: str | None = None
    _pulses: int | None = None
    _counter: int | None = None
    _delay: int | None = None
    _power: int | None = None
    _energy: float | None = None

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        if (
            self._counter is not None
            or self._power is not None
            or self._energy is not None
        ):
            return ["sensor"]
        return ["binary_sensor", "button"]

    def is_counter_channel(self) -> bool:
        """Return if this channel is a counter channel."""
        return (
            self._counter is not None
            or self._power is not None
            or self._energy is not None
        )

    def get_sensor_types(self) -> list[str]:
        """Return flow/gas, flow/water, or power/energy keys for counter channels."""
        if not self.is_counter_channel():
            return []
        if self.is_gas():
            return ["flow", "gas"]
        if self.is_water():
            return ["flow", "water"]
        return ["power", "energy"]

    @property
    def energy(self) -> float | None:
        """Return the accumulated energy in kWh, or None if not yet received."""
        if self._energy is not None:
            return round(self._energy / 1000, 3)
        if (
            self._counter is not None
            and self._pulses
            and self._Unit == ENERGY_KILO_WATT_HOUR
        ):
            return round(self._counter / self._pulses, 2)
        return None

    def get_counter_total(self) -> float | None:
        """Return the accumulated counter total in its native unit (kWh, m³ or L)."""
        if self._energy is not None:
            return round(self._energy / 1000, 3)
        if self._counter is not None and self._pulses:
            return round(self._counter / self._pulses, 2)
        return None

    def _rate_from_pulse_interval(self) -> float:
        """Return the instantaneous rate derived from the interval between pulses.

        Only VMB8IN-20 maps a CounterValueMessage, so on every other counter
        module _power stays None and the rate has to be derived from _delay.
        """
        # if we don't know the delay or the pulses
        # or we don't know the unit
        # or the delay is the max value
        #   we always return 0
        if (
            not self._delay
            or not self._pulses
            or not self._Unit
            or self._delay == 0xFFFF
        ):
            return round(0, 2)
        if self._Unit in {VOLUME_LITERS_HOUR, VOLUME_CUBIC_METER_HOUR}:
            return round((1000 * 3600) / (self._delay * self._pulses), 2)
        if self._Unit == ENERGY_KILO_WATT_HOUR:
            return round((1000 * 1000 * 3600) / (self._delay * self._pulses), 2)
        return round(0, 2)

    def get_state(self) -> float:
        """Return the current state of the counter."""
        if self._energy is not None:
            return self._energy
        return self._rate_from_pulse_interval()

    def get_unit(self) -> str | None:
        """Return the unit of the counter."""
        if self._Unit == VOLUME_LITERS_HOUR:
            return "L"
        if self._Unit == VOLUME_CUBIC_METER_HOUR:
            return "m3"
        if self._Unit == ENERGY_KILO_WATT_HOUR:
            return "W"
        return None

    def set_unit(self, unit: str) -> None:
        """Set the unit of the counter."""
        if unit == "liter":
            unit = VOLUME_LITERS_HOUR
        elif unit in {"m3", "m³"}:
            unit = VOLUME_CUBIC_METER_HOUR
        self._Unit = unit

    def get_counter_state(self) -> int:
        """Return the instantaneous power (or flow) of the counter.

        Falls back to the pulse interval when the module does not report
        _power; returning the accumulated counter here would duplicate the
        energy property.
        """
        if self._power is not None:
            return self._power
        return int(self._rate_from_pulse_interval())

    def get_counter_unit(self) -> str:
        """Return the unit of the counter."""
        return self._Unit or ""

    def is_water(self) -> bool:
        """Return if this channel is a water channel."""
        return bool(self._counter and self._Unit == VOLUME_LITERS_HOUR)

    def is_gas(self) -> bool:
        """Return if this channel is a gas channel."""
        return bool(self._counter and self._Unit == VOLUME_CUBIC_METER_HOUR)

    def is_electricity(self) -> bool:
        """Return if this channel is an electricity channel."""
        return self._Unit == ENERGY_KILO_WATT_HOUR


class Sensor(Button):
    """A Sensor channel.

    This is a bit weird, but this happens because of code sharing with openhab
    A sensor in this case is actually a Button
    """

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        if self._enabled:
            return ["binary_sensor", "led"]
        return []


class ThermostatChannel(Button):
    """A Thermostat channel.

    These are the booster/heater/alarms
    """
