"""Test cases for the Memo channel class"""

from unittest.mock import Mock, patch

import pytest

from velbusaio.channels import Memo


class TestMemo:
    """Test cases for the Memo channel class."""

    @pytest.mark.asyncio
    async def test_set_short_text(self, mock_module, mock_writer):
        """Test setting short memo text."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg.memo_text = ""
            mock_msg_class.return_value = mock_msg

            memo = Memo(mock_module, 1, "Memo", False, True, mock_writer, 0x01)
            await memo.set("Test")

            # Should be called once for short text
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_long_text(self, mock_module, mock_writer):
        """Test setting long memo text."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class

            def create_msg(*args, **kwargs):
                msg = Mock()
                msg.memo_text = ""
                msg.start = 0
                return msg

            mock_msg_class.side_effect = create_msg

            memo = Memo(mock_module, 1, "Memo", False, True, mock_writer, 0x01)
            await memo.set("This is a long text message")

            # Should be called multiple times for long text (chunks of 5)
            assert mock_writer.call_count > 1
