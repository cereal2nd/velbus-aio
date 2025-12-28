"""
Test cases for VelbusProtocol buffer_updated method (network/buffered protocol)
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from velbusaio.protocol import VelbusProtocol
from velbusaio.raw_message import RawMessage


class TestVelbusProtocolBufferUpdated:
    """Test cases for buffer_updated method (network/buffered protocol)."""

    @pytest.mark.asyncio
    async def test_buffer_updated_valid_message(self):
        """Test buffer_updated with valid message."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        # Simulate received data in buffer
        valid_message = b"\x0f\xf8\x01\x00\x00\x00\x00\x00\x06\x04"
        protocol._buffer[: len(valid_message)] = valid_message

        with patch("velbusaio.protocol.create_message_info") as mock_create:
            mock_msg = Mock(spec=RawMessage)
            mock_create.return_value = (mock_msg, b"")

            protocol.buffer_updated(len(valid_message))

            await asyncio.sleep(0.1)

            callback.assert_called_once_with(mock_msg)

    @pytest.mark.asyncio
    async def test_buffer_updated_partial_message(self):
        """Test buffer_updated with partial message."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        # Partial message (too short)
        partial_message = b"\x0f\xf8\x01"
        protocol._buffer[: len(partial_message)] = partial_message

        with patch("velbusaio.protocol.create_message_info") as mock_create:
            protocol.buffer_updated(len(partial_message))

            await asyncio.sleep(0.1)

            # Should not try to create message if too short
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_buffer_updated_updates_activity_time(self):
        """Test that buffer_updated updates last activity time."""
        import time

        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        protocol._last_activity_time = 0

        protocol.buffer_updated(10)

        assert protocol._last_activity_time > 0

    @pytest.mark.asyncio
    async def test_buffer_updated_creates_new_buffer(self):
        """Test that buffer_updated creates new buffer with remaining data."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        # Valid message with some remaining data
        valid_message = b"\x0f\xf8\x01\x00\x00\x00\x00\x00\x06\x04"
        remaining = b"\x0f\xf8\x02"
        combined = valid_message + remaining

        protocol._buffer[: len(combined)] = combined

        with patch("velbusaio.protocol.create_message_info") as mock_create:
            mock_msg = Mock(spec=RawMessage)
            mock_create.return_value = (mock_msg, remaining)

            old_buffer = protocol._buffer
            protocol.buffer_updated(len(combined))

            await asyncio.sleep(0.1)

            # Buffer should be renewed
            assert protocol._buffer is not old_buffer
            assert protocol._buffer_pos == len(remaining)

    @pytest.mark.asyncio
    async def test_buffer_updated_position_tracking(self):
        """Test that buffer position is tracked correctly."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        initial_pos = protocol._buffer_pos
        bytes_received = 2  # Use small number to avoid triggering message processing

        protocol.buffer_updated(bytes_received)

        # Should have added bytes_received to position (if no message processing triggered)
        # Since we're using 2 bytes which is less than MINIMUM_MESSAGE_SIZE, no processing occurs
        assert protocol._buffer_pos == initial_pos + bytes_received
