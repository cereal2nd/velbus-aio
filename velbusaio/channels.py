"""Velbusaio channel classes.

author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import math
import string
from typing import TYPE_CHECKING, Any

from velbusaio.baseItem import BaseItem
from velbusaio.command_registry import commandRegistry
from velbusaio.config import ConfigParameter
from velbusaio.const import (
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    TEMP_CELSIUS,
    VOLUME_CUBIC_METER_HOUR,
    VOLUME_LITERS_HOUR,
)
from velbusaio.exceptions import VelbusConfigError
from velbusaio.message import Message
from velbusaio.messages.edge_set_color import (
    CustomColorPriority,
    SetCustomColorMessage,
    SetEdgeColorMessage,
)
from velbusaio.messages.sensor_temp_request import (
    TEMP_AUTOSEND_DISABLED,
    TEMP_AUTOSEND_INTERVAL_MAX,
    TEMP_AUTOSEND_INTERVAL_MIN,
    TEMP_AUTOSEND_ON_CHANGE,
)

if TYPE_CHECKING:
    from velbusaio.actions import ActionSlot
    from velbusaio.module import Module


class Channel(BaseItem):
    """A velbus channel.

    This is the basic abstract class of a velbus channel
    Each specific channel type (Relay, Dimmer, Temperature, etc.) will inherit from this class
    and implement its own specific methods and attributes.
    """

    def __init__(
        self,
        module: Module,
        num: int,
        name: str,
        nameEditable: bool,
        subDevice: bool,
        writer: Callable[[Message], Awaitable[None]],
        address: int,
    ):
        """Initialize the channel."""
        super().__init__(module, name, writer)
        self._num = num
        self._subDevice = subDevice
        if not nameEditable:
            self._is_loaded = True
        else:
            self._is_loaded = False
        self._address = address
        self._name_parts = {}

    def get_identifier(self) -> str:
        """Return the identifier of the entity."""
        if not self.is_sub_device():
            return str(self.get_module_address())
        return f"{self.get_module_address()}-{self.get_channel_number()}"

    def get_module_address(self, chan_type: str = "") -> int:
        """Return (sub)module address for channel."""
        if chan_type == "Button" and self._num > 24:
            return self._module.get_addresses()[3]
        if chan_type == "Button" and self._num > 16:
            return self._module.get_addresses()[2]
        if chan_type == "Button" and self._num > 8:
            return self._module.get_addresses()[1]
        return self._address

    def get_channel_number(self) -> int:
        """Return channel number."""
        return self._num

    def set_loaded(self, loaded: bool) -> None:
        """Set if this channel is loaded."""
        self._is_loaded = loaded

    def is_loaded(self) -> bool:
        """Is this channel loaded."""
        return self._is_loaded

    def is_counter_channel(self) -> bool:
        """Return if this channel is a counter channel."""
        return False

    def is_temperature(self) -> bool:
        """Return if this channel is a temperature sensor."""
        return False

    def set_sub_device(self, sub_device: bool) -> None:
        """Set if this channel is a subdevice."""
        self._subDevice = sub_device

    def is_sub_device(self) -> bool:
        """Return if this channel is a subdevice."""
        return self._subDevice

    def set_name_char(self, pos: int, char: int) -> None:
        """Set a char of the channel name."""
        self._is_loaded = True
        self._name_parts = {}
        # make sure the string is long enough
        while len(self._name) < int(pos):
            self._name += " "
        # store the char on correct pos
        self._name = self._name[: int(pos)] + chr(char) + self._name[int(pos) + 1 :]

    def set_name_part(self, part: int, name: str) -> bool:
        """Set a part of the channel name. Returns True if name is now complete."""
        # if int(part) not in self._name_parts:
        #    return
        self._name_parts[int(part)] = name
        if len(self._name_parts) == 3:
            self._generate_name()
            return True
        return False

    def _generate_name(self) -> None:
        """Generate the channel name if all 3 parts are received."""
        name = self._name_parts[1] + self._name_parts[2] + self._name_parts[3]
        self._name = "".join(filter(lambda x: x in string.printable, name))
        self._is_loaded = True
        self._name_parts = {}

    def __getstate__(self):
        """Get channel state for pickling."""
        d = self.__dict__
        return {
            k: d[k]
            for k in d
            if k not in {"_writer", "_on_status_update", "_name_parts"}
        }

    def to_cache(self) -> dict:
        """Get channel state for caching."""
        dst = {
            "name": self._name,
            "type": type(self).__name__,
            "subdevice": self._subDevice,
        }
        if hasattr(self, "_Unit"):
            dst["Unit"] = self._Unit
        return dst

    def __setstate__(self, state):
        """Restore channel from cached state."""
        self.__dict__.update(state)
        self._on_status_update = []
        self._name_parts = {}

    def __repr__(self) -> str:
        """Representation of this channel."""
        items = []
        for k, v in self.__dict__.items():
            if k not in ["_module", "_writer", "_name_parts", "_class"]:
                items.append(f"{k} = {v!r}")
        return "{}[{}]".format(type(self), ", ".join(items))

    def __str__(self) -> str:
        """String representation of this channel."""
        return self.__repr__()

    def get_channel_info(self) -> dict[str, Any]:
        """Get the channel info as a dictionary."""
        data = {}
        data["type"] = self.__class__.__name__
        for key, value in self.__dict__.items():
            if key not in ["_module", "_writer", "_name_parts", "_on_status_update"]:
                data[key.replace("_", "", 1)] = value
        return data

    async def update(self, data: dict) -> None:
        """Set the attributes of this channel."""
        changed = False
        for key, new_val in data.items():
            cur_val = getattr(self, f"_{key}", None)
            if cur_val != new_val:
                setattr(self, f"_{key}", new_val)
                changed = True
        if changed:
            await self.status_update()

    async def status_update(self) -> None:
        """Call all registered status update methods."""
        for m in self._on_status_update:
            await m()

    def get_categories(self) -> list[str]:
        """Get the categories (mainly for home-assistant).

        COMPONENT_TYPES = ["switch", "sensor", "binary_sensor", "cover", "climate", "light"]
        """
        return []

    def on_status_update(self, meth: Callable[[], Awaitable[None]]) -> None:
        """Register a method to be called on status update."""
        self._on_status_update.append(meth)

    def remove_on_status_update(self, meth: Callable[[], Awaitable[None]]) -> None:
        """Remove a method from the status update callbacks."""
        self._on_status_update.remove(meth)

    def get_counter_state(self) -> int:
        """Return the current state of the counter."""
        raise NotImplementedError

    def get_counter_unit(self) -> str:
        """Return the unit of the counter."""
        raise NotImplementedError

    def get_max(self) -> int | None:
        """Return the maximum value."""
        raise NotImplementedError

    def get_min(self) -> int | None:
        """Return the minimum value."""
        raise NotImplementedError

    def is_water(self) -> bool:
        """Return if this channel is a water channel."""
        return False

    async def press(self) -> None:
        """Simulate a press action on this channel."""
        raise NotImplementedError

    def get_sensor_type(self) -> str | None:
        """Return the sensor type."""
        return None

    @property
    def energy(self) -> float | None:
        """Return the accumulated energy in kWh, or None if not applicable."""
        return None

    def get_action_table(self):
        """Return this channel's action table, if available."""
        return self._module.get_action_table(self._num)

    async def get_actions(
        self, *, refresh: bool = False, include_empty: bool = False
    ) -> list[ActionSlot]:
        """Return programmed input→output action slots for this channel."""
        table = self.get_action_table()
        if table is None:
            return []
        return await table.get_actions(refresh=refresh, include_empty=include_empty)

    async def set_action(
        self,
        *,
        source_address: int,
        action: str | int,
        source_channel: int | None = None,
        source_bit: int | None = None,
        time1: int = 0xFF,
        time2: int = 0xFF,
        time3: int = 0xFF,
        time4: int = 0xFF,
        on_release: bool = False,
        slot: int | None = None,
    ) -> ActionSlot:
        """Program an input→output action on this channel."""
        table = self.get_action_table()
        if table is None:
            raise RuntimeError(f"Channel {self._num} has no action table")
        return await table.set_action(
            source_address=source_address,
            action=action,
            source_channel=source_channel,
            source_bit=source_bit,
            time1=time1,
            time2=time2,
            time3=time3,
            time4=time4,
            on_release=on_release,
            slot=slot,
        )

    async def clear_action(self, slot: int) -> ActionSlot:
        """Clear one action slot on this channel."""
        table = self.get_action_table()
        if table is None:
            raise RuntimeError(f"Channel {self._num} has no action table")
        return await table.clear_action(slot)

    async def clear_actions_for_source(
        self,
        source_address: int,
        *,
        source_channel: int | None = None,
        source_bit: int | None = None,
    ) -> list[ActionSlot]:
        """Clear action slots matching a source input."""
        table = self.get_action_table()
        if table is None:
            return []
        return await table.clear_actions_for_source(
            source_address,
            source_channel=source_channel,
            source_bit=source_bit,
        )


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
        """Return if position reporting is supported."""
        # position will be populated after the first BlindStatusNgMessage (during module load)
        # For VMBxBL modules, position will remain None and not be overwritten
        return self._position is not None

    async def open(self) -> None:
        """Open the blind."""
        cls = commandRegistry.get_command(0x05, self._module.get_type())
        msg = cls(self._address)
        msg.channel = self._num
        await self._writer(msg)

    async def close(self) -> None:
        """Close the blind."""
        cls = commandRegistry.get_command(0x06, self._module.get_type())
        msg = cls(self._address)
        msg.channel = self._num
        await self._writer(msg)

    async def stop(self) -> None:
        """Stop the blind."""
        cls = commandRegistry.get_command(0x04, self._module.get_type())
        msg = cls(self._address)
        msg.channel = self._num
        await self._writer(msg)

    async def set_position(self, position: int) -> None:
        """Set the blind to a specific position."""
        # may not be supported by the module
        if position == 100:
            # at least VMB1BLS ignores command 0x1C with position 0x64
            await self.close()
            return
        cls = commandRegistry.get_command(0x1C, self._module.get_type())
        msg = cls(self._address)
        msg.channel = self._num
        msg.position = position
        await self._writer(msg)


class Button(Channel):
    """A Button channel."""

    _enabled = True
    _closed = False
    _led_state = None
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
            value = (
                self._saved_reaction_time
                if self._saved_reaction_time not in (None, spec["disabled_value"])
                else spec["enabled_value"]
            )
        else:
            value = spec["disabled_value"]
        await memory.write_byte(spec["address"], value & 0xFF)
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
        cls = commandRegistry.get_command(code, self._module.get_type())
        msg = cls(_mod_add)
        msg.leds = [_chn_num]
        await self._writer(msg)
        await self.update({"led_state": state})

    async def press(self) -> None:
        """Press the button."""
        _mod_add = self.get_module_address("Button")
        _chn_num = self._num - self._module.calc_channel_offset(_mod_add)
        # send the just pressed
        cls = commandRegistry.get_command(0x00, self._module.get_type())
        msg = cls(_mod_add)
        msg.closed = [_chn_num]
        await self._writer(msg)
        # wait
        await asyncio.sleep(0.3)
        # send the just released
        msg = cls(_mod_add)
        msg.opened = [_chn_num]
        await self._writer(msg)


class ButtonCounter(Button):
    """A ButtonCounter channel.

    This channel can act as a button and as a counter
    => standard     this is the calculated power value
    => is_counter   this is the numeric energy value
    """

    _Unit: str | None = None
    _pulses = None
    _counter = None
    _delay = None
    _power = None
    _energy = None

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

    def get_sensor_type(self) -> str | None:
        """Return the sensor type."""
        if self._counter:
            return "counter"
        return None

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

    def get_state(self) -> int:
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
        self._Unit = unit

    def get_counter_state(self) -> int:
        """Return the instantaneous power (or flow) of the counter.

        Falls back to the pulse interval when the module does not report
        _power; returning the accumulated counter here would duplicate the
        energy property.
        """
        if self._power:
            return self._power
        return self._rate_from_pulse_interval()

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
    ):
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
        cls = commandRegistry.get_command(0x07, self._module.get_type())
        msg = cls(self._address)
        msg.dimmer_state = int(slider * self.slider_scale / 100)
        msg.dimmer_transitiontime = int(transitiontime)
        msg.dimmer_channels = [self._num]
        await self._writer(msg)

    async def restore_dimmer_state(self, transitiontime: int = 0) -> None:
        """Restore dimmer to last known state."""
        cls = commandRegistry.get_command(0x11, self._module.get_type())
        msg = cls(self._address)
        msg.dimmer_transitiontime = int(transitiontime)
        msg.dimmer_channels = [self._num]
        await self._writer(msg)


class Temperature(Channel):
    """A Temperature sensor channel."""

    _cur = 0
    _cur_precision = None
    _max = None
    _min = None
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

    def get_sensor_type(self):
        """Return the sensor type."""
        return "temperature"

    def is_temperature(self) -> bool:
        """Return if this channel is a temperature sensor."""
        return True

    def get_max(self) -> int | None:
        """Return the maximum temperature recorded."""
        if self._max is None:
            return None
        return round(self._max, 2)

    def get_min(self) -> int | None:
        """Return the minimum temperature recorded."""
        if self._min is None:
            return None
        return round(self._min, 2)

    def get_climate_target(self) -> int:
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
        cls = commandRegistry.get_command(0xE4, self._module.get_type())
        msg = cls(self._address)
        msg.temp = temp
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
        cls = commandRegistry.get_command(0xE5, self._module.get_type())
        msg = cls(self._address, interval)
        await self._writer(msg)

    def get_temp_settings(self):
        """Return the module temperature settings helper, if available."""
        if self._module is None:
            return None
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
        cls = commandRegistry.get_command(code, self._module.get_type())
        msg = cls(self._address, sleep)
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
        cls = commandRegistry.get_command(code, self._module.get_type())
        msg = cls(self._address)
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


class SensorNumber(Channel):
    """A Numeric Sensor channel."""

    _cur = 0
    _unit = None
    _sensor_type = None

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        return ["sensor"]

    def get_class(self) -> None:
        """Return the device class for this channel."""
        return

    def get_unit(self) -> None:
        """Return the unit of measurement for this channel."""
        return self._unit

    def get_state(self) -> float:
        """Return the current state of the temperature sensor."""
        return round(self._cur, 2)

    def get_sensor_type(self) -> str | None:
        """Return the sensor type."""
        return self._sensor_type


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
        return commandRegistry.has_command(0x16, self._module.get_type())

    def supports_forced_on(self) -> bool:
        """Return True when forced-on / cancel-forced-on commands are available."""
        return commandRegistry.has_command(0x14, self._module.get_type())

    def supports_forced_off(self) -> bool:
        """Return True when forced-off / cancel-forced-off commands are available."""
        return commandRegistry.has_command(0x12, self._module.get_type())

    async def turn_on(self) -> None:
        """Send the turn on message."""
        cls = commandRegistry.get_command(0x02, self._module.get_type())
        msg = cls(self._address)
        msg.relay_channels = [self._num]
        await self._writer(msg)

    async def turn_off(self) -> None:
        """Send the turn off message."""
        cls = commandRegistry.get_command(0x01, self._module.get_type())
        msg = cls(self._address)
        msg.relay_channels = [self._num]
        await self._writer(msg)

    async def set_forced_on(self, state: bool) -> None:
        """Set or cancel forced on."""
        code = 0x14 if state else 0x15
        cls = commandRegistry.get_command(code, self._module.get_type())
        msg = cls(self._address)
        msg.channel = self._num
        if state:
            msg.delay_time = 0xFFFFFF  # Permanent
        await self._writer(msg)

    async def set_forced_off(self, state: bool) -> None:
        """Set or cancel forced off."""
        code = 0x12 if state else 0x13
        cls = commandRegistry.get_command(code, self._module.get_type())
        msg = cls(self._address)
        msg.channel = self._num
        if state:
            msg.delay_time = 0xFFFFFF  # Permanent
        await self._writer(msg)

    async def set_inhibit(self, state: bool) -> None:
        """Set or cancel inhibit."""
        code = 0x16 if state else 0x17
        cls = commandRegistry.get_command(code, self._module.get_type())
        msg = cls(self._address)
        msg.channel = self._num
        if state:
            msg.delay_time = 0xFFFFFF  # Permanent
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


class EdgeLit(Channel):
    """An EdgeLit channel."""

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        return ["light"]

    async def reset_color(self, left=True, top=True, right=True, bottom=True):
        """Send the edgelit color message."""
        msg = SetEdgeColorMessage(self._address)
        msg.apply_background_color = True
        msg.color_idx = 0
        msg.apply_to_left_edge = left
        msg.apply_to_top_edge = top
        msg.apply_to_right_edge = right
        msg.apply_to_bottom_edge = bottom
        msg.apply_to_all_pages = True
        await self._writer(msg)

    async def set_color(
        self,
        color_idx: int,
        left=True,
        top=True,
        right=True,
        bottom=True,
        blinking=False,
        priority=CustomColorPriority.LOW_PRIORITY,
    ) -> None:
        """Send the set color message."""

        msg = SetEdgeColorMessage(self._address)
        msg.apply_background_color = True
        msg.background_blinking = blinking
        msg.color_idx = color_idx
        msg.apply_to_left_edge = left
        msg.apply_to_top_edge = top
        msg.apply_to_right_edge = right
        msg.apply_to_bottom_edge = bottom
        msg.apply_to_all_pages = True
        msg.custom_color_priority = priority
        await self._writer(msg)

    async def set_rgbw(
        self,
        red: int,
        green: int,
        blue: int,
        white: int,
        left=False,
        top=False,
        right=False,
        bottom=False,
    ) -> None:
        """Set RGBW color for specific edges using a dedicated palette index per side."""
        # Mapping sides to palette indices
        if left:
            palette_idx = 1
        elif top:
            palette_idx = 2
        elif right:
            palette_idx = 3
        elif bottom:
            palette_idx = 4
        else:
            return  # No side specified

        # If all components are 0, we turn the edge OFF by using the default black palette (Index 0)
        if red == 0 and green == 0 and blue == 0 and white == 0:
            msg_apply = SetEdgeColorMessage(self._address)
            msg_apply.apply_background_color = True
            msg_apply.custom_color_palette = False  # USE DEFAULT PALETTE
            msg_apply.color_idx = 0  # BLACK
            msg_apply.apply_to_left_edge = left
            msg_apply.apply_to_top_edge = top
            msg_apply.apply_to_right_edge = right
            msg_apply.apply_to_bottom_edge = bottom
            msg_apply.apply_to_all_pages = True
            await self._writer(msg_apply)
            return

        # 1. Update the custom palette color
        msg_palette = SetCustomColorMessage(self._address)
        msg_palette.palette_idx = palette_idx
        msg_palette.red = red
        msg_palette.green = green
        msg_palette.blue = blue
        # If white is provided, we enable the official white_mode
        # This tells the module to use its internal white settings
        msg_palette.white_mode = white > 128
        msg_palette.saturation = 127  # Max saturation
        await self._writer(msg_palette)

        # 2. Apply this custom palette index to the requested edge
        msg_apply = SetEdgeColorMessage(self._address)
        msg_apply.apply_background_color = True
        msg_apply.custom_color_palette = True  # USE CUSTOM PALETTE
        msg_apply.color_idx = palette_idx
        msg_apply.apply_to_left_edge = left
        msg_apply.apply_to_top_edge = top
        msg_apply.apply_to_right_edge = right
        msg_apply.apply_to_bottom_edge = bottom
        msg_apply.apply_to_all_pages = True
        await self._writer(msg_apply)
