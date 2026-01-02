"""Test cases for the Dimmer channel class"""

from unittest.mock import Mock, patch

import pytest

from velbusaio.channels import Dimmer


class TestDimmer:
    """Test cases for the Dimmer channel class."""

    def test_init_default_scale(self, mock_module, mock_writer):
        """Test dimmer initialization with default scale."""
        dimmer = Dimmer(mock_module, 1, "Dimmer", False, True, mock_writer, 0x01)
        assert dimmer.slider_scale == 100

    def test_init_custom_scale(self, mock_module, mock_writer):
        """Test dimmer initialization with custom scale."""
        dimmer = Dimmer(
            mock_module, 1, "Dimmer", False, True, mock_writer, 0x01, slider_scale=254
        )
        assert dimmer.slider_scale == 254

    def test_get_categories(self, mock_module, mock_writer):
        """Test dimmer categories."""
        dimmer = Dimmer(mock_module, 1, "Dimmer", False, True, mock_writer, 0x01)
        assert dimmer.get_categories() == ["light"]

    @pytest.mark.asyncio
    async def test_is_on_when_on(self, mock_module, mock_writer):
        """Test checking if dimmer is on."""
        dimmer = Dimmer(mock_module, 1, "Dimmer", False, True, mock_writer, 0x01)
        await dimmer.update({"state": 50})
        assert dimmer.is_on()

    @pytest.mark.asyncio
    async def test_is_on_when_off(self, mock_module, mock_writer):
        """Test checking if dimmer is off."""
        dimmer = Dimmer(mock_module, 1, "Dimmer", False, True, mock_writer, 0x01)
        await dimmer.update({"state": 0})
        assert not dimmer.is_on()

    @pytest.mark.asyncio
    async def test_get_dimmer_state(self, mock_module, mock_writer):
        """Test getting dimmer state as percentage."""
        dimmer = Dimmer(mock_module, 1, "Dimmer", False, True, mock_writer, 0x01)
        await dimmer.update({"state": 50})
        assert dimmer.get_dimmer_state() == 50

    @pytest.mark.asyncio
    async def test_get_dimmer_state_with_custom_scale(self, mock_module, mock_writer):
        """Test getting dimmer state with custom scale."""
        dimmer = Dimmer(
            mock_module, 1, "Dimmer", False, True, mock_writer, 0x01, slider_scale=254
        )
        await dimmer.update({"state": 127})
        assert dimmer.get_dimmer_state() == 50

    @pytest.mark.asyncio
    async def test_set_dimmer_state(self, mock_module, mock_writer):
        """Test setting dimmer state."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            dimmer = Dimmer(mock_module, 1, "Dimmer", False, True, mock_writer, 0x01)
            await dimmer.set_dimmer_state(75, transitiontime=5)

            mock_registry.get_command.assert_called_once_with(0x07, 0x01)
            assert mock_msg.dimmer_state == 75
            assert mock_msg.dimmer_transitiontime == 5
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_dimmer_state(self, mock_module, mock_writer):
        """Test restoring dimmer to last known state."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            dimmer = Dimmer(mock_module, 1, "Dimmer", False, True, mock_writer, 0x01)
            await dimmer.restore_dimmer_state(transitiontime=3)

            mock_registry.get_command.assert_called_once_with(0x11, 0x01)
            assert mock_msg.dimmer_transitiontime == 3
            mock_writer.assert_called_once()
