"""Test cases for the SelectedProgram channel class"""

from unittest.mock import Mock, patch

import pytest

from velbusaio.channels import SelectedProgram
from velbusaio.messages.module_status import PROGRAM_SELECTION


class TestSelectedProgram:
    """Test cases for the SelectedProgram channel class."""

    def test_get_categories(self, mock_module, mock_writer):
        """Test selected program categories."""
        prog = SelectedProgram(
            mock_module, 1, "Program", False, True, mock_writer, 0x01
        )
        assert prog.get_categories() == ["select"]

    def test_get_class(self, mock_module, mock_writer):
        """Test getting selected program class."""
        prog = SelectedProgram(
            mock_module, 1, "Program", False, True, mock_writer, 0x01
        )
        assert prog.get_class() is None

    def test_get_options(self, mock_module, mock_writer):
        """Test getting available program options."""
        prog = SelectedProgram(
            mock_module, 1, "Program", False, True, mock_writer, 0x01
        )
        assert prog.get_options() == list(PROGRAM_SELECTION.values())

    @pytest.mark.asyncio
    async def test_get_selected_program(self, mock_module, mock_writer):
        """Test getting selected program."""
        prog = SelectedProgram(
            mock_module, 1, "Program", False, True, mock_writer, 0x01
        )
        await prog.update({"selected_program_str": "Program 1"})
        assert prog.get_selected_program() == "Program 1"

    @pytest.mark.asyncio
    async def test_set_selected_program(self, mock_module, mock_writer):
        """Test setting selected program."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg_class.return_value = mock_msg

            prog = SelectedProgram(
                mock_module, 1, "Program", False, True, mock_writer, 0x01
            )
            program_name = list(PROGRAM_SELECTION.values())[0]
            await prog.set_selected_program(program_name)

            mock_registry.get_command.assert_called_once_with(0xB3, 0x01)
            mock_writer.assert_called_once()
