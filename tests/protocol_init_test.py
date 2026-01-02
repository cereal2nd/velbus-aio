"""Test cases for VelbusProtocol initialization"""

from unittest.mock import AsyncMock, Mock

from velbusaio.protocol import VelbusProtocol


class TestVelbusProtocolInit:
    """Test cases for VelbusProtocol initialization."""

    def test_init(self):
        """Test protocol initialization."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        assert protocol._message_received_callback == callback
        assert protocol._buffer_pos == 0
        assert protocol._serial_buf == b""
        assert protocol.transport is None
        assert not protocol._closing
        assert protocol._send_queue is not None
        assert (
            protocol._restart_writer is False
        )  # Not started until transport connected
        assert protocol._connection_state_callback is None

    def test_init_with_connection_callback(self):
        """Test protocol initialization with connection state callback."""
        msg_callback = AsyncMock()
        conn_callback = Mock()
        protocol = VelbusProtocol(msg_callback, conn_callback)

        assert protocol._message_received_callback == msg_callback
        assert protocol._connection_state_callback == conn_callback

    def test_buffer_initialization(self):
        """Test that buffer is properly initialized."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        assert len(protocol._buffer) > 0
        assert protocol._buffer_view is not None
        assert protocol._buffer_pos == 0
