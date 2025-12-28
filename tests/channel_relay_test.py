"""
Test cases for the Relay channel class
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from velbusaio.channels import Relay


class TestRelay:
    """Test cases for the Relay channel class."""

    def test_get_categories_enabled(self, mock_module, mock_writer):
        """Test relay categories when enabled."""
        relay = Relay(mock_module, 1, "Relay", False, True, mock_writer, 0x01)
        assert relay.get_categories() == ["switch"]

    @pytest.mark.asyncio
    async def test_get_categories_disabled(self, mock_module, mock_writer):
        """Test relay categories when disabled."""
        relay = Relay(mock_module, 1, "Relay", False, True, mock_writer, 0x01)
        await relay.update({"enabled": False})
        assert relay.get_categories() == []

    @pytest.mark.asyncio
    async def test_is_on(self, mock_module, mock_writer):
        """Test checking if relay is on."""
        relay = Relay(mock_module, 1, "Relay", False, True, mock_writer, 0x01)
        await relay.update({"on": True})
        assert relay.is_on()

        await relay.update({"on": False})
        assert not relay.is_on()

    @pytest.mark.asyncio
    async def test_is_inhibit(self, mock_module, mock_writer):
        """Test checking if relay is inhibited."""
        relay = Relay(mock_module, 1, "Relay", False, True, mock_writer, 0x01)
        await relay.update({"inhibit": True})
        assert relay.is_inhibit()

    @pytest.mark.asyncio
    async def test_is_forced_on(self, mock_module, mock_writer):
        """Test checking if relay is forced on."""
        relay = Relay(mock_module, 1, "Relay", False, True, mock_writer, 0x01)
        await relay.update({"forced_on": True})
        assert relay.is_forced_on()

    @pytest.mark.asyncio
    async def test_is_disabled(self, mock_module, mock_writer):
        """Test checking if relay is disabled."""
        relay = Relay(mock_module, 1, "Relay", False, True, mock_writer, 0x01)
        await relay.update({"disabled": True})
        assert relay.is_disabled()

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_module, mock_writer):
        """Test turning relay on."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg.relay_channels = []
            mock_msg_class.return_value = mock_msg

            relay = Relay(mock_module, 1, "Relay", False, True, mock_writer, 0x01)
            await relay.turn_on()

            mock_registry.get_command.assert_called_once_with(0x02, 0x01)
            assert 1 in mock_msg.relay_channels
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_module, mock_writer):
        """Test turning relay off."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg.relay_channels = []
            mock_msg_class.return_value = mock_msg

            relay = Relay(mock_module, 1, "Relay", False, True, mock_writer, 0x01)
            await relay.turn_off()

            mock_registry.get_command.assert_called_once_with(0x01, 0x01)
            assert 1 in mock_msg.relay_channels
            mock_writer.assert_called_once()
