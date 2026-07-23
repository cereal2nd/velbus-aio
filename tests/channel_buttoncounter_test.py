"""Test cases for the ButtonCounter channel class"""

import pytest

from velbusaio.channels import ButtonCounter
from velbusaio.const import (
    ENERGY_KILO_WATT_HOUR,
    VOLUME_CUBIC_METER_HOUR,
    VOLUME_LITERS_HOUR,
)


class TestButtonCounter:
    """Test cases for the ButtonCounter channel class."""

    def test_get_categories_counter_mode(self, mock_module, mock_writer):
        """Test button counter categories in counter mode."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 100
        assert button.get_categories() == ["sensor"]

    def test_get_categories_counter_mode_zero(self, mock_module, mock_writer):
        """Test button counter categories when counter value is zero."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 0
        assert button.get_categories() == ["sensor"]

    def test_get_categories_button_mode(self, mock_module, mock_writer):
        """Test button counter categories in button mode (no data received yet)."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        # _counter=None means no counter status received; channel acts as button
        assert button._counter is None
        assert button.get_categories() == ["binary_sensor", "button"]

    def test_is_counter_channel(self, mock_module, mock_writer):
        """Test checking if channel is counter."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 100
        assert button.is_counter_channel()

        button._counter = None
        assert not button.is_counter_channel()

    def test_is_counter_channel_zero_counter(self, mock_module, mock_writer):
        """Test that a zero counter value still classifies as a counter channel."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 0
        assert button.is_counter_channel()

    @pytest.mark.asyncio
    async def test_is_long_pressed(self, mock_module, mock_writer):
        """Test inherited long-press state accessor."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        await button.update({"long": True})
        assert button.is_long_pressed()

        await button.update({"long": False})
        assert not button.is_long_pressed()

    def test_get_sensor_type_counter(self, mock_module, mock_writer):
        """Test getting sensor type for counter."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = True
        assert button.get_sensor_type() == "counter"

        button._counter = False
        assert button.get_sensor_type() is None

    def test_get_state_with_energy(self, mock_module, mock_writer):
        """Test getting state with energy value."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._energy = 150.5
        assert button.get_state() == 150.5

    def test_get_state_liters_per_hour(self, mock_module, mock_writer):
        """Test getting state for liters per hour."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = VOLUME_LITERS_HOUR
        button._delay = 1000
        button._pulses = 10
        expected = (1000 * 3600) / (1000 * 10)
        assert button.get_state() == round(expected, 2)

    def test_get_state_cubic_meter_per_hour(self, mock_module, mock_writer):
        """Test getting state for cubic meters per hour."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = VOLUME_CUBIC_METER_HOUR
        button._delay = 1000
        button._pulses = 10
        expected = (1000 * 3600) / (1000 * 10)
        assert button.get_state() == round(expected, 2)

    def test_get_state_kwh(self, mock_module, mock_writer):
        """Test getting state for kilowatt hours."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = ENERGY_KILO_WATT_HOUR
        button._delay = 1000
        button._pulses = 10
        expected = (1000 * 1000 * 3600) / (1000 * 10)
        assert button.get_state() == round(expected, 2)

    def test_get_state_no_delay(self, mock_module, mock_writer):
        """Test getting state when delay is not set."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = VOLUME_LITERS_HOUR
        button._delay = None
        assert button.get_state() == 0

    def test_get_state_max_delay(self, mock_module, mock_writer):
        """Test getting state when delay is max value."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = VOLUME_LITERS_HOUR
        button._delay = 0xFFFF
        button._pulses = 10
        assert button.get_state() == 0

    def test_get_unit_liters(self, mock_module, mock_writer):
        """Test getting unit for liters."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = VOLUME_LITERS_HOUR
        assert button.get_unit() == "L"

    def test_get_unit_cubic_meter(self, mock_module, mock_writer):
        """Test getting unit for cubic meters."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = VOLUME_CUBIC_METER_HOUR
        assert button.get_unit() == "m3"

    def test_get_unit_kwh(self, mock_module, mock_writer):
        """Test getting unit for kilowatt hours."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = ENERGY_KILO_WATT_HOUR
        assert button.get_unit() == "W"

    def test_get_counter_state_with_power(self, mock_module, mock_writer):
        """Test getting counter state with power value."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._power = 250.5
        assert button.get_counter_state() == 250.5

    def test_get_counter_state_calculated(self, mock_module, mock_writer):
        """Test the counter state is derived from the pulse interval."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = ENERGY_KILO_WATT_HOUR
        button._counter = 1000
        button._pulses = 10
        button._delay = 1000
        expected = (1000 * 1000 * 3600) / (1000 * 10)
        assert button.get_counter_state() == round(expected, 2)

    def test_get_counter_state_differs_from_energy(self, mock_module, mock_writer):
        """A module without CounterValueMessage must not report power == energy.

        Modules such as the VMB7IN only send a CounterStatusMessage, so _power
        and _energy stay None. Both values used to fall back to counter/pulses,
        which made the power and energy sensors in Home Assistant identical.
        """
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = ENERGY_KILO_WATT_HOUR
        button._counter = 1000
        button._pulses = 10
        button._delay = 1000
        assert button._power is None
        assert button._energy is None
        assert button.get_counter_state() != button.energy

    def test_get_counter_state_without_delay(self, mock_module, mock_writer):
        """Test the counter state is 0 while the pulse interval is unknown."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = ENERGY_KILO_WATT_HOUR
        button._counter = 1000
        button._pulses = 10
        assert button.get_counter_state() == 0

    def test_get_state_without_pulses(self, mock_module, mock_writer):
        """Test the rate is 0 instead of raising when the pulses are unknown."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = ENERGY_KILO_WATT_HOUR
        button._delay = 1000
        assert button.get_state() == 0

    def test_get_counter_unit(self, mock_module, mock_writer):
        """Test getting counter unit."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._Unit = VOLUME_LITERS_HOUR
        assert button.get_counter_unit() == VOLUME_LITERS_HOUR

    def test_is_water(self, mock_module, mock_writer):
        """Test checking if counter is water meter."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 100
        button._Unit = VOLUME_LITERS_HOUR
        assert button.is_water()

        button._Unit = ENERGY_KILO_WATT_HOUR
        assert not button.is_water()

    def test_energy_from_energy_field(self, mock_module, mock_writer):
        """Test energy property returns kWh from _energy field (Wh)."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._energy = 100000  # 100000 Wh = 100.0 kWh
        assert button.energy == 100.0

    def test_energy_zero(self, mock_module, mock_writer):
        """Test energy property when _energy is zero (valid reading, not unknown)."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._energy = 0
        assert button.energy == 0.0

    def test_energy_none_when_not_received(self, mock_module, mock_writer):
        """Test energy property returns None when no energy data received yet."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        assert button.energy is None

    def test_energy_fallback_for_kwh_counter(self, mock_module, mock_writer):
        """Test energy property fallback to pulse-based calc for kWh counters."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 1000
        button._pulses = 10
        button._Unit = ENERGY_KILO_WATT_HOUR
        assert button.energy == round(1000 / 10, 2)

    def test_energy_fallback_not_used_for_water(self, mock_module, mock_writer):
        """Test energy property does not use pulse-based calc for water counters."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 1000
        button._pulses = 10
        button._Unit = VOLUME_LITERS_HOUR
        assert button.energy is None


# Sensor Tests
