"""
Test cases for the EdgeLit channel class
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from velbusaio.channels import EdgeLit


class TestEdgeLit:
    """Test cases for the EdgeLit channel class."""

    @pytest.mark.asyncio
    async def test_reset_color(self, mock_module, mock_writer):
        """Test resetting edge color."""
        edge = EdgeLit(mock_module, 1, "Edge", False, True, mock_writer, 0x01)
        await edge.reset_color(left=True, top=False, right=True, bottom=False)

        mock_writer.assert_called_once()
        msg = mock_writer.call_args[0][0]
        assert msg.apply_background_color is True
        assert msg.apply_to_left_edge is True
        assert msg.apply_to_top_edge is False
        assert msg.apply_to_right_edge is True
        assert msg.apply_to_bottom_edge is False

    @pytest.mark.asyncio
    async def test_set_color(self, mock_module, mock_writer):
        """Test setting edge color."""
        edge = EdgeLit(mock_module, 1, "Edge", False, True, mock_writer, 0x01)
        await edge.set_color(
            5, left=True, top=True, right=False, bottom=False, blinking=True
        )

        mock_writer.assert_called_once()
        msg = mock_writer.call_args[0][0]
        assert msg.color_idx == 5
        assert msg.background_blinking is True
        assert msg.apply_to_left_edge is True
        assert msg.apply_to_top_edge is True
        assert msg.apply_to_right_edge is False
        assert msg.apply_to_bottom_edge is False


# Memo Tests
