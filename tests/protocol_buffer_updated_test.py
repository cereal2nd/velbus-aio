"""Test cases for VelbusProtocol buffer_updated method (network/buffered protocol)"""

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

        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        protocol._last_activity_time = 0

        protocol.buffer_updated(10)

        assert protocol._last_activity_time > 0

    @pytest.mark.asyncio
    async def test_buffer_updated_keeps_remaining_data(self):
        """Test that data left after a parsed message is kept for the next read."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        # Valid message followed by the start of a second (incomplete) message
        valid_message = b"\x0f\xf8\x01\x00\x00\x00\x00\x00\x06\x04"
        remaining = b"\x0f\xf8\x02"
        combined = valid_message + remaining

        protocol._buffer[: len(combined)] = combined

        with patch("velbusaio.protocol.create_message_info") as mock_create:
            mock_msg = Mock(spec=RawMessage)
            mock_create.return_value = (mock_msg, remaining)

            protocol.buffer_updated(len(combined))

            await asyncio.sleep(0.1)

            # The leftover (partial second message) must be preserved, not dropped,
            # so it can be completed by the next read.
            assert protocol._serial_buf == remaining

    @pytest.mark.asyncio
    async def test_buffer_updated_accumulates_partial_data(self):
        """Test that bytes below the minimum size are accumulated, not processed."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        bytes_received = 2  # Less than MINIMUM_MESSAGE_SIZE, so no processing occurs

        protocol.buffer_updated(bytes_received)

        # The received bytes are accumulated in _serial_buf awaiting more data.
        assert len(protocol._serial_buf) == bytes_received
