"""Test cases for the LightSensor channel class"""

import pytest

from velbusaio.channels import LightSensor
from velbusaio.const import DEVICE_CLASS_ILLUMINANCE


class TestLightSensor:
    """Test cases for the LightSensor channel class."""

    def test_get_categories(self, mock_module, mock_writer):
        """Test light sensor categories."""
        sensor = LightSensor(mock_module, 1, "Light", False, True, mock_writer, 0x01)
        assert sensor.get_categories() == ["sensor"]

    def test_get_class(self, mock_module, mock_writer):
        """Test getting light sensor class."""
        sensor = LightSensor(mock_module, 1, "Light", False, True, mock_writer, 0x01)
        assert sensor.get_class() == DEVICE_CLASS_ILLUMINANCE

    def test_get_unit(self, mock_module, mock_writer):
        """Test getting light sensor unit."""
        sensor = LightSensor(mock_module, 1, "Light", False, True, mock_writer, 0x01)
        assert sensor.get_unit() is None

    @pytest.mark.asyncio
    async def test_get_state(self, mock_module, mock_writer):
        """Test getting light sensor state."""
        sensor = LightSensor(mock_module, 1, "Light", False, True, mock_writer, 0x01)
        await sensor.update({"cur": 125.5})
        assert sensor.get_state() == 125.5


# Relay Tests
