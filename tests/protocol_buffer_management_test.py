"""
Test cases for VelbusProtocol buffer management methods
"""

from unittest.mock import AsyncMock

import pytest

from velbusaio.const import MAXIMUM_MESSAGE_SIZE
from velbusaio.protocol import VelbusProtocol


class TestVelbusProtocolBufferManagement:
    """Test cases for buffer management methods."""

    def test_get_buffer(self):
        """Test getting buffer for reading."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        buffer_view = protocol.get_buffer(100)

        assert isinstance(buffer_view, memoryview)
        assert len(buffer_view) <= MAXIMUM_MESSAGE_SIZE

    def test_get_buffer_with_position(self):
        """Test getting buffer when position is not zero."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        protocol._buffer_pos = 10
        buffer_view = protocol.get_buffer(100)

        # Should return view from current position
        assert isinstance(buffer_view, memoryview)
        assert len(buffer_view) == MAXIMUM_MESSAGE_SIZE - 10

    def test_new_buffer_without_remaining(self):
        """Test creating new buffer without remaining data."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        old_buffer = protocol._buffer
        protocol._new_buffer()

        assert protocol._buffer is not old_buffer
        assert protocol._buffer_pos == 0
        assert len(protocol._buffer) == MAXIMUM_MESSAGE_SIZE

    def test_new_buffer_with_remaining(self):
        """Test creating new buffer with remaining data."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        remaining_data = b"\x0f\xf8\x01\x02\x03"
        old_buffer = protocol._buffer

        protocol._new_buffer(remaining_data)

        assert protocol._buffer is not old_buffer
        assert protocol._buffer_pos == len(remaining_data)
        assert protocol._buffer[: len(remaining_data)] == remaining_data

    def test_new_buffer_creates_correct_size(self):
        """Test that new buffer has correct size."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        protocol._new_buffer()

        assert len(protocol._buffer) == MAXIMUM_MESSAGE_SIZE
