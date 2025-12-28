"""
Test cases for the SensorNumber channel class
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from velbusaio.channels import SensorNumber


class TestSensorNumber:
    """Test cases for the SensorNumber channel class."""

    def test_get_categories(self, mock_module, mock_writer):
        """Test sensor number categories."""
        sensor = SensorNumber(mock_module, 1, "Sensor", False, True, mock_writer, 0x01)
        assert sensor.get_categories() == ["sensor"]

    def test_get_class(self, mock_module, mock_writer):
        """Test getting sensor class."""
        sensor = SensorNumber(mock_module, 1, "Sensor", False, True, mock_writer, 0x01)
        assert sensor.get_class() is None

    @pytest.mark.asyncio
    async def test_get_unit(self, mock_module, mock_writer):
        """Test getting sensor unit."""
        sensor = SensorNumber(mock_module, 1, "Sensor", False, True, mock_writer, 0x01)
        await sensor.update({"unit": "°C"})
        assert sensor.get_unit() == "°C"

    @pytest.mark.asyncio
    async def test_get_state(self, mock_module, mock_writer):
        """Test getting sensor state."""
        sensor = SensorNumber(mock_module, 1, "Sensor", False, True, mock_writer, 0x01)
        await sensor.update({"cur": 42.75})
        assert sensor.get_state() == 42.75

    @pytest.mark.asyncio
    async def test_get_sensor_type(self, mock_module, mock_writer):
        """Test getting sensor type."""
        sensor = SensorNumber(mock_module, 1, "Sensor", False, True, mock_writer, 0x01)
        await sensor.update({"sensor_type": "humidity"})
        assert sensor.get_sensor_type() == "humidity"


# LightSensor Tests
