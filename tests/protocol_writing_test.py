"""Test cases for VelbusProtocol writing functionality"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from velbusaio.protocol import VelbusProtocol


class TestVelbusProtocolWriting:
    """Test cases for writing and pause/restart functionality."""

    @pytest.mark.asyncio
    async def test_pause_writing(self):
        """Test pausing writing."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        protocol._restart_writer = True
        protocol._writer_task = Mock()

        await protocol.pause_writing()

        assert protocol._restart_writer is False

    def test_restart_writing(self):
        """Test restarting writing."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        protocol._restart_writer = True

        with patch("asyncio.ensure_future") as mock_ensure_future:
            protocol.restart_writing()

            mock_ensure_future.assert_called_once()

    def test_restart_writing_when_locked(self):
        """Test restarting writing when lock is held."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        protocol._restart_writer = True
        protocol._write_transport_lock._locked = True

        with patch("asyncio.ensure_future") as mock_ensure_future:
            protocol.restart_writing()

            # Should not restart when locked
            mock_ensure_future.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending a message."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_message = Mock()
        mock_message.to_bytes.return_value = b"\x0f\x01"

        await protocol.send_message(mock_message)

        # Message should be in queue
        assert protocol._send_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_write_message_success(self):
        """Test writing a message successfully."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_transport = Mock()
        mock_transport.is_closing.return_value = False
        protocol.transport = mock_transport

        mock_message = Mock()
        mock_message.to_bytes.return_value = b"\x0f\x01\x02"

        result = await protocol._write_message(mock_message)

        assert result is True
        mock_transport.write.assert_called_once_with(b"\x0f\x01\x02")

    @pytest.mark.asyncio
    async def test_write_message_transport_closing(self):
        """Test writing a message when transport is closing."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_transport = Mock()
        mock_transport.is_closing.return_value = True
        protocol.transport = mock_transport

        mock_message = Mock()

        # Call the undecorated implementation to avoid the backoff retry
        # decorator, which would otherwise cause the test to wait.
        result = await protocol._write_message.__wrapped__(protocol, mock_message)

        assert result is False
        mock_transport.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_write_auth_key(self):
        """Test writing authentication key."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_transport = Mock()
        mock_transport.is_closing.return_value = False
        protocol.transport = mock_transport

        await protocol.write_auth_key("test_key_123")

        mock_transport.write.assert_called_once_with(b"test_key_123")

    def test_calculate_queue_sleep_time_normal(self):
        """Test calculating sleep time for normal message."""
        mock_message = Mock()
        mock_message.rtr = False
        mock_message.command = 0x01

        sleep_time = VelbusProtocol._calculate_queue_sleep_time(mock_message, 0.001)

        assert sleep_time > 0

    def test_calculate_queue_sleep_time_rtr(self):
        """Test calculating sleep time for RTR message."""
        from velbusaio.const import SLEEP_TIME

        mock_message = Mock()
        mock_message.rtr = True
        mock_message.command = 0x01

        sleep_time = VelbusProtocol._calculate_queue_sleep_time(mock_message, 0.001)

        assert sleep_time >= SLEEP_TIME - 0.001

    def test_calculate_queue_sleep_time_channel_name_request(self):
        """Test calculating sleep time for channel name request (0xEF)."""
        from velbusaio.const import SLEEP_TIME

        mock_message = Mock()
        mock_message.rtr = False
        mock_message.command = 0xEF

        sleep_time = VelbusProtocol._calculate_queue_sleep_time(mock_message, 0.001)

        # Should be longer for channel name request
        assert sleep_time >= SLEEP_TIME * 33 - 0.001

    def test_calculate_queue_sleep_time_already_late(self):
        """Test calculating sleep time when send already took too long."""
        from velbusaio.const import SLEEP_TIME

        mock_message = Mock()
        mock_message.rtr = False
        mock_message.command = 0x01

        sleep_time = VelbusProtocol._calculate_queue_sleep_time(
            mock_message, SLEEP_TIME + 1
        )

        assert sleep_time == 0

    @pytest.mark.asyncio
    async def test_wait_on_all_messages_sent_async(self):
        """Test waiting for all messages to be sent."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        # Add a message and immediately mark as done
        await protocol._send_queue.put(Mock())
        protocol._send_queue.task_done()

        # Should complete without hanging
        await asyncio.wait_for(protocol.wait_on_all_messages_sent_async(), timeout=1.0)
