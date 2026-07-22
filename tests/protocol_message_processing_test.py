"""Test cases for VelbusProtocol message processing"""

from unittest.mock import AsyncMock, Mock

import pytest

from velbusaio.message import ParserError
from velbusaio.protocol import VelbusProtocol
from velbusaio.raw_message import RawMessage


class TestVelbusProtocolMessageProcessing:
    """Test cases for message processing."""

    @pytest.mark.asyncio
    async def test_process_message(self):
        """Test processing a message."""
        callback = AsyncMock()
        protocol = VelbusProtocol(callback)

        mock_message = Mock(spec=RawMessage)

        await protocol._process_message(mock_message)

        callback.assert_called_once_with(mock_message)

    @pytest.mark.asyncio
    async def test_process_message_callback_exception(self):
        """Test that exceptions in callback are handled gracefully."""
        callback = AsyncMock(side_effect=Exception("Test error"))
        protocol = VelbusProtocol(callback)

        mock_message = Mock(spec=RawMessage)

        # Should not raise exception
        with pytest.raises(Exception):
            await protocol._process_message(mock_message)

    @pytest.mark.asyncio
    async def test_process_message_parser_error_swallowed(self):
        """A ParserError from a short/malformed packet must not escape the task.

        _process_message is scheduled as a detached task, so a raised
        ParserError would surface as an unretrieved task exception. It must be
        caught and logged instead.
        """
        callback = AsyncMock(
            side_effect=ParserError("ModuleStatusMessage2 needs 6 bytes of data have 4")
        )
        protocol = VelbusProtocol(callback)

        mock_message = Mock(spec=RawMessage)

        # Should not raise
        await protocol._process_message(mock_message)
        callback.assert_called_once_with(mock_message)
