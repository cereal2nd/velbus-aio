"""Test cases for the Blind channel class"""

from unittest.mock import Mock, patch

import pytest

from velbusaio.channels import Blind
from velbusaio.command_registry import commandRegistry

VMB1BL = 0x03
VMB2BLE_10 = 0x4A


class TestBlind:
    """Test cases for the Blind channel class."""

    def test_get_categories(self, mock_module, mock_writer):
        """Test blind categories."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        assert blind.get_categories() == ["cover"]

    @pytest.mark.asyncio
    async def test_get_position(self, mock_module, mock_writer):
        """Test getting blind position."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        await blind.update({"position": 50})
        assert blind.get_position() == 50

    @pytest.mark.asyncio
    async def test_get_state(self, mock_module, mock_writer):
        """Test getting blind state."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        await blind.update({"state": 0x01})
        assert blind.get_state() == 0x01

    @pytest.mark.asyncio
    async def test_is_opening(self, mock_module, mock_writer):
        """Test checking if blind is opening."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        await blind.update({"state": 0x01})
        assert blind.is_opening()
        assert not blind.is_closing()
        assert not blind.is_stopped()

    @pytest.mark.asyncio
    async def test_is_closing(self, mock_module, mock_writer):
        """Test checking if blind is closing."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        await blind.update({"state": 0x02})
        assert blind.is_closing()
        assert not blind.is_opening()
        assert not blind.is_stopped()

    @pytest.mark.asyncio
    async def test_is_stopped(self, mock_module, mock_writer):
        """Test checking if blind is stopped."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        await blind.update({"state": 0x00})
        assert blind.is_stopped()
        assert not blind.is_opening()
        assert not blind.is_closing()

    @pytest.mark.asyncio
    async def test_is_closed_with_position(self, mock_module, mock_writer):
        """Test checking if blind is closed when position is known."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        await blind.update({"position": 100})
        assert blind.is_closed()

        await blind.update({"position": 50})
        assert not blind.is_closed()

    def test_is_closed_without_position(self, mock_module, mock_writer):
        """Test checking if blind is closed when position is unknown."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        assert blind.is_closed() is None

    @pytest.mark.asyncio
    async def test_is_open_with_position(self, mock_module, mock_writer):
        """Test checking if blind is open when position is known."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        await blind.update({"position": 0})
        assert blind.is_open()

        await blind.update({"position": 50})
        assert not blind.is_open()

    def test_is_open_without_position(self, mock_module, mock_writer):
        """Test checking if blind is open when position is unknown."""
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        assert blind.is_open() is None

    def test_support_position_vmb2ble_without_reported_position(
        self, mock_module, mock_writer
    ):
        """NG blind modules expose position support before status arrives."""
        commandRegistry.register_module_commands(
            VMB2BLE_10, {"1C": "CoverPosMessage"}
        )
        mock_module.get_type.return_value = VMB2BLE_10
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        assert blind.support_position()

    def test_support_position_vmb1bl(self, mock_module, mock_writer):
        """Legacy blind modules without 0x1C do not support position."""
        commandRegistry.register_module_commands(
            VMB1BL, {"EC": "BlindStatusMessage"}
        )
        mock_module.get_type.return_value = VMB1BL
        blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
        assert not blind.support_position()

    @pytest.mark.asyncio
    async def test_open(self, mock_module, mock_writer):
        """Test opening blind."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
            await blind.open()

            mock_registry.get_command.assert_called_once_with(0x05, 0x01)
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, mock_module, mock_writer):
        """Test closing blind."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
            await blind.close()

            mock_registry.get_command.assert_called_once_with(0x06, 0x01)
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self, mock_module, mock_writer):
        """Test stopping blind."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
            await blind.stop()

            mock_registry.get_command.assert_called_once_with(0x04, 0x01)
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_position(self, mock_module, mock_writer):
        """Test setting blind position."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
            await blind.set_position(50)

            mock_registry.get_command.assert_called_once_with(0x1C, 0x01)
            assert mock_msg.position == 50
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_position_fully_closed(self, mock_module, mock_writer):
        """Test setting blind position to fully closed uses close command."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            blind = Blind(mock_module, 1, "Blind", False, True, mock_writer, 0x01)
            await blind.set_position(100)

            # Should use close command (0x06) instead of position command
            mock_registry.get_command.assert_called_once_with(0x06, 0x01)
