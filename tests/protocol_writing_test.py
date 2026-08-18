"""Test cases for VelbusProtocol writing functionality"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from velbusaio.controller import Velbus
from velbusaio.protocol import VelbusProtocol


class TestVelbusProtocolWriting:
    """Test cases for writing functionality."""

    def test_write_message_success(self):
        """Test writing a message successfully."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_transport = Mock()
        mock_transport.is_closing.return_value = False
        protocol.transport = mock_transport

        mock_message = Mock()
        mock_message.to_bytes.return_value = b"\x0f\x01\x02"

        result = protocol.write_message(mock_message)

        assert result is True
        mock_transport.write.assert_called_once_with(b"\x0f\x01\x02")

    def test_write_message_transport_closing(self):
        """Test writing a message when transport is closing."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_transport = Mock()
        mock_transport.is_closing.return_value = True
        protocol.transport = mock_transport

        mock_message = Mock()

        result = protocol.write_message(mock_message)

        assert result is False
        mock_transport.write.assert_not_called()

    def test_connection_made_sends_auth_key(self):
        """Test automatic authentication key transmission when connection is established."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback, auth_key="test_key_123")

        mock_transport = Mock()
        protocol.connection_made(mock_transport)

        mock_transport.write.assert_called_once_with(b"test_key_123")

    def test_connection_made_without_auth_key(self):
        """Test no authentication key transmitted on connection_made when auth_key is None."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback, auth_key=None)

        mock_transport = Mock()
        protocol.connection_made(mock_transport)

        mock_transport.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_flow_control_pause_resume(self):
        """Test pause_writing and resume_writing flow control events."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_transport = Mock()
        protocol.connection_made(mock_transport)
        assert protocol._can_write.is_set()

        protocol.pause_writing()
        assert not protocol._can_write.is_set()

        protocol.resume_writing()
        assert protocol._can_write.is_set()

    def test_calculate_queue_sleep_time_normal(self):
        """Test calculating sleep time for normal message."""
        mock_message = Mock()
        mock_message.rtr = False
        mock_message.command = 0x01

        sleep_time = Velbus._calculate_queue_sleep_time(mock_message, 0.001)

        assert sleep_time > 0

    def test_calculate_queue_sleep_time_rtr(self):
        """Test calculating sleep time for RTR message."""
        from velbusaio.const import SLEEP_TIME

        mock_message = Mock()
        mock_message.rtr = True
        mock_message.command = 0x01

        sleep_time = Velbus._calculate_queue_sleep_time(mock_message, 0.001)

        assert sleep_time >= SLEEP_TIME - 0.001

    def test_calculate_queue_sleep_time_channel_name_request(self):
        """Test calculating sleep time for channel name request (0xEF)."""
        from velbusaio.const import SLEEP_TIME

        mock_message = Mock()
        mock_message.rtr = False
        mock_message.command = 0xEF

        sleep_time = Velbus._calculate_queue_sleep_time(mock_message, 0.001)

        assert sleep_time >= SLEEP_TIME * 33 - 0.001

    def test_calculate_queue_sleep_time_already_late(self):
        """Test calculating sleep time when send already took too long."""
        from velbusaio.const import SLEEP_TIME

        mock_message = Mock()
        mock_message.rtr = False
        mock_message.command = 0x01

        sleep_time = Velbus._calculate_queue_sleep_time(
            mock_message, SLEEP_TIME + 1
        )

        assert sleep_time == 0

    @pytest.mark.asyncio
    async def test_wait_on_all_messages_sent_async(self):
        """Test waiting for all messages to be sent in controller."""
        velbus = Velbus("")

        await velbus._send_queue.put(Mock())
        velbus._send_queue.task_done()

        await asyncio.wait_for(velbus.wait_on_all_messages_sent_async(), timeout=1.0)

    @pytest.mark.asyncio
    async def test_send_loop_retry_on_disconnect(self):
        """Test that send loop retries sending a message if connection drops before sending."""
        velbus = Velbus("")
        mock_protocol = Mock()
        mock_protocol.is_connected = False
        mock_protocol.wait_can_write = AsyncMock()

        send_task = asyncio.create_task(velbus._send_loop())

        mock_msg = Mock()
        mock_msg.rtr = False
        mock_msg.command = 0x01
        await velbus._send_queue.put(mock_msg)

        await asyncio.sleep(0.05)
        assert velbus._send_queue.qsize() == 1

        velbus._protocol = mock_protocol
        mock_protocol.write_message.return_value = True
        velbus._is_connected = True
        mock_protocol.is_connected = True
        velbus._connected_event.set()

        await asyncio.wait_for(velbus.wait_on_all_messages_sent_async(), timeout=1.0)

        mock_protocol.write_message.assert_called_once_with(mock_msg)
        await velbus.stop()
