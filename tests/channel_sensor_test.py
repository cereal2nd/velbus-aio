"""
Test cases for the Sensor channel class
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from velbusaio.channels import Sensor


class TestSensor:
    """Test cases for the Sensor channel class."""

    def test_get_categories_enabled(self, mock_module, mock_writer):
        """Test sensor categories when enabled."""
        sensor = Sensor(mock_module, 1, "Sensor", False, True, mock_writer, 0x01)
        assert sensor.get_categories() == ["binary_sensor", "led"]

    @pytest.mark.asyncio
    async def test_get_categories_disabled(self, mock_module, mock_writer):
        """Test sensor categories when disabled."""
        sensor = Sensor(mock_module, 1, "Sensor", False, True, mock_writer, 0x01)
        await sensor.update({"enabled": False})
        assert sensor.get_categories() == []


# Dimmer Tests
