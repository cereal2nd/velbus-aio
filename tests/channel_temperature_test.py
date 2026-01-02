"""Test cases for the Temperature channel class"""

from unittest.mock import Mock, patch

import pytest

from velbusaio.channels import Temperature
from velbusaio.const import DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS


class TestTemperature:
    """Test cases for the Temperature channel class."""

    def test_get_categories_thermostat(self, mock_module, mock_writer):
        """Test temperature categories for thermostat."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        temp._thermostat = True
        assert temp.get_categories() == ["sensor", "climate"]

    def test_get_categories_sensor_only(self, mock_module, mock_writer):
        """Test temperature categories for sensor only."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        temp._thermostat = False
        assert temp.get_categories() == ["sensor"]

    def test_get_class(self, mock_module, mock_writer):
        """Test getting temperature class."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        assert temp.get_class() == DEVICE_CLASS_TEMPERATURE

    def test_get_unit(self, mock_module, mock_writer):
        """Test getting temperature unit."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        assert temp.get_unit() == TEMP_CELSIUS

    @pytest.mark.asyncio
    async def test_get_state(self, mock_module, mock_writer):
        """Test getting temperature state."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        await temp.update({"cur": 21.5})
        assert temp.get_state() == 21.5

    def test_get_sensor_type(self, mock_module, mock_writer):
        """Test getting sensor type."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        assert temp.get_sensor_type() == "temperature"

    def test_is_temperature(self, mock_module, mock_writer):
        """Test checking if channel is temperature."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        assert temp.is_temperature()

    @pytest.mark.asyncio
    async def test_get_max(self, mock_module, mock_writer):
        """Test getting maximum temperature."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        await temp.update({"max": 30.5})
        assert temp.get_max() == 30.5

    def test_get_max_none(self, mock_module, mock_writer):
        """Test getting maximum when not set."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        assert temp.get_max() is None

    @pytest.mark.asyncio
    async def test_get_min(self, mock_module, mock_writer):
        """Test getting minimum temperature."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        await temp.update({"min": 15.5})
        assert temp.get_min() == 15.5

    def test_get_min_none(self, mock_module, mock_writer):
        """Test getting minimum when not set."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        assert temp.get_min() is None

    @pytest.mark.asyncio
    async def test_get_climate_target(self, mock_module, mock_writer):
        """Test getting climate target temperature."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        await temp.update({"target": 22.0})
        assert temp.get_climate_target() == 22.0

    @pytest.mark.asyncio
    async def test_get_climate_preset(self, mock_module, mock_writer):
        """Test getting climate preset mode."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        await temp.update({"cmode": "comfort"})
        assert temp.get_climate_preset() == "comfort"

    @pytest.mark.asyncio
    async def test_get_climate_mode(self, mock_module, mock_writer):
        """Test getting climate operating mode."""
        temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
        await temp.update({"cstatus": "run"})
        assert temp.get_climate_mode() == "run"

    @pytest.mark.asyncio
    async def test_set_temp(self, mock_module, mock_writer):
        """Test setting temperature."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
            await temp.set_temp(22.5)

            mock_registry.get_command.assert_called_once_with(0xE4, 0x01)
            assert mock_msg.temp == 45.0  # 22.5 * 2
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_preset_comfort(self, mock_module, mock_writer):
        """Test setting preset to comfort mode."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
            temp._cstatus = "run"
            await temp.set_preset("comfort")

            mock_registry.get_command.assert_called_once_with(0xDB, 0x01)

    @pytest.mark.asyncio
    async def test_set_climate_mode(self, mock_module, mock_writer):
        """Test setting climate operating mode."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
            temp._cmode = "comfort"
            await temp.set_climate_mode("manual")

            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_mode_heat(self, mock_module, mock_writer):
        """Test setting mode to heat."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
            await temp.set_mode("heat")

            mock_registry.get_command.assert_called_once_with(0xE0, 0x01)

    @pytest.mark.asyncio
    async def test_set_mode_cool(self, mock_module, mock_writer):
        """Test setting mode to cool."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            temp = Temperature(mock_module, 1, "Temp", False, True, mock_writer, 0x01)
            await temp.set_mode("cool")

            mock_registry.get_command.assert_called_once_with(0xDF, 0x01)
