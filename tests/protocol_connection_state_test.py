"""
Test cases for VelbusProtocol connection state management
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from velbusaio.protocol import VelbusProtocol


class TestVelbusProtocolConnectionState:
    """Test cases for connection state management."""

    def test_add_connection_state_callback(self):
        """Test adding connection state callback."""
        msg_callback = AsyncMock()
        initial_callback = Mock()
        protocol = VelbusProtocol(msg_callback, initial_callback)

        new_callback = Mock()
        protocol.add_connection_state_callback(new_callback)

        # Verify callback was added
        assert new_callback in protocol._connection_state_callbacks

    def test_remove_connection_state_callback(self):
        """Test removing connection state callback."""
        msg_callback = AsyncMock()
        callback_to_remove = Mock()
        protocol = VelbusProtocol(msg_callback, callback_to_remove)

        protocol.remove_connection_state_callback(callback_to_remove)

        # Verify callback was removed
        assert callback_to_remove not in protocol._connection_state_callbacks

    def test_notify_connection_state_callbacks(self):
        """Test notifying connection state callbacks."""
        msg_callback = AsyncMock()
        conn_callback1 = Mock()
        conn_callback2 = Mock()

        protocol = VelbusProtocol(msg_callback, conn_callback1)
        protocol.add_connection_state_callback(conn_callback2)

        protocol._notify_connection_state_callbacks(True)

        conn_callback1.assert_called_once_with(True)
        conn_callback2.assert_called_once_with(True)

    def test_notify_connection_state_callbacks_handles_exceptions(self):
        """Test that exceptions in callbacks don't crash the protocol."""
        msg_callback = AsyncMock()
        bad_callback = Mock(side_effect=Exception("Test error"))
        good_callback = Mock()

        protocol = VelbusProtocol(msg_callback, bad_callback)
        protocol.add_connection_state_callback(good_callback)

        # Should not raise exception
        protocol._notify_connection_state_callbacks(True)

        # Good callback should still be called
        good_callback.assert_called_once_with(True)

    def test_connection_made(self):
        """Test connection_made callback."""
        callback = AsyncMock()
        conn_callback = Mock()
        protocol = VelbusProtocol(callback, conn_callback)

        mock_transport = Mock()

        with patch.object(protocol, "restart_writing") as mock_restart:
            protocol.connection_made(mock_transport)

            assert protocol.transport == mock_transport
            assert protocol._restart_writer is True
            mock_restart.assert_called()
            conn_callback.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_connection_lost_with_exception(self):
        """Test connection_lost with exception."""
        callback = AsyncMock()
        conn_callback = Mock()
        protocol = VelbusProtocol(callback, conn_callback)

        mock_transport = Mock()
        protocol.transport = mock_transport

        exc = Exception("Connection error")

        with patch.object(protocol, "pause_writing", new_callable=AsyncMock):
            protocol.connection_lost(exc)

            await asyncio.sleep(0.1)  # Allow async tasks to run

            assert protocol.transport is None
            conn_callback.assert_called_once_with(False)

    @pytest.mark.asyncio
    async def test_connection_lost_eof(self):
        """Test connection_lost with EOF (None exception)."""
        callback = AsyncMock()
        conn_callback = Mock()
        protocol = VelbusProtocol(callback, conn_callback)

        mock_transport = Mock()
        protocol.transport = mock_transport

        with patch.object(protocol, "pause_writing", new_callable=AsyncMock):
            protocol.connection_lost(None)

            await asyncio.sleep(0.1)

            assert protocol.transport is None
            conn_callback.assert_called_once_with(False)

    def test_connection_lost_while_closing(self):
        """Test connection_lost when protocol is closing."""
        callback = AsyncMock()
        conn_callback = Mock()
        protocol = VelbusProtocol(callback, conn_callback)

        protocol._closing = True
        mock_transport = Mock()
        protocol.transport = mock_transport

        protocol.connection_lost(Exception("Test"))

        # Callback should not be called when closing
        conn_callback.assert_not_called()

    def test_close(self):
        """Test closing the protocol."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_transport = Mock()
        protocol.transport = mock_transport

        protocol.close()

        assert protocol._closing is True
        assert protocol._restart_writer is False
        mock_transport.close.assert_called_once()

    def test_close_without_transport(self):
        """Test closing when no transport exists."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        # Should not raise exception
        protocol.close()

        assert protocol._closing is True
        assert protocol._restart_writer is False
