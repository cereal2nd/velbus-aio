"""Test cases for the ButtonCounter channel class"""

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
        button._counter = True
        assert button.get_categories() == ["sensor"]

    def test_get_categories_button_mode(self, mock_module, mock_writer):
        """Test button counter categories in button mode."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = False
        assert button.get_categories() == ["binary_sensor", "button"]

    def test_is_counter_channel(self, mock_module, mock_writer):
        """Test checking if channel is counter."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = True
        assert button.is_counter_channel()

        button._counter = False
        assert not button.is_counter_channel()

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
        """Test getting calculated counter state."""
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 1000
        button._pulses = 10
        assert button.get_counter_state() == 100.0

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
        button._counter = True
        button._Unit = VOLUME_LITERS_HOUR
        assert button.is_water()

        button._Unit = ENERGY_KILO_WATT_HOUR
        assert not button.is_water()


# Sensor Tests
