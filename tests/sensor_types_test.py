"""Tests for get_sensor_types on sensor items."""

import pytest

from velbusaio.channels import Temperature
from velbusaio.properties import (
    LightValue,
    PSUCurrent,
    PSULoad,
    PSUPower,
    PSUVoltage,
)


class TestSensorTypes:
    """Integrator sensor type keys."""

    def test_temperature_types(self, mock_module, mock_writer):
        """Temperature channels use the temperature key."""
        channel = Temperature(
            mock_module, 1, "Temp", False, True, mock_writer, 0x01
        )
        assert channel.get_sensor_types() == ["temperature"]

    def test_light_value_types(self, mock_module, mock_writer):
        """Light sensors use the measurement key."""
        prop = LightValue(mock_module, "Light", mock_writer)
        assert prop.get_sensor_types() == ["measurement"]

    def test_psu_voltage_types(self, mock_module, mock_writer):
        prop = PSUVoltage(mock_module, "V", mock_writer)
        assert prop.get_sensor_types() == ["voltage"]

    def test_psu_current_types(self, mock_module, mock_writer):
        prop = PSUCurrent(mock_module, "A", mock_writer)
        assert prop.get_sensor_types() == ["current"]

    def test_psu_power_types(self, mock_module, mock_writer):
        prop = PSUPower(mock_module, "W", mock_writer)
        assert prop.get_sensor_types() == ["power"]

    def test_psu_load_types(self, mock_module, mock_writer):
        prop = PSULoad(mock_module, "Load", mock_writer)
        assert prop.get_sensor_types() == ["load"]
