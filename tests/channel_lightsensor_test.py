"""Test cases for the LightSensor channel class"""

import pytest

from velbusaio.properties import LightValue
from velbusaio.const import DEVICE_CLASS_ILLUMINANCE


class TestLightSensor:
    """Test cases for the LightSensor channel class."""

    def test_get_categories(self, mock_module, mock_writer):
        """Test light sensor categories."""
        sensor = LightValue(mock_module, "Light", mock_writer)
        assert sensor.get_categories() == ["sensor"]

    @pytest.mark.asyncio
    async def test_get_state(self, mock_module, mock_writer):
        """Test getting light sensor state."""
        sensor = LightValue(mock_module, "Light", mock_writer)
        await sensor.update({"cur": 125.5})
        assert sensor.get_state() == 125.5
