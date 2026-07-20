"""Unit tests for the channel-name and memo-text message classes."""

from __future__ import annotations

from velbusaio.const import PRIORITY_LOW
from velbusaio.messages.channel_name_part1 import (
    ChannelNamePart1Message,
    ChannelNamePart1Message2,
    ChannelNamePart1Message3,
)
from velbusaio.messages.channel_name_part2 import (
    ChannelNamePart2Message,
    ChannelNamePart2Message2,
    ChannelNamePart2Message3,
)
from velbusaio.messages.channel_name_part3 import (
    ChannelNamePart3Message,
    ChannelNamePart3Message2,
    ChannelNamePart3Message3,
)
from velbusaio.messages.memo_text import MemoTextMessage


class TestChannelNamePart1Message:
    """Tests for ChannelNamePart1Message."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart1Message()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]) + b"NAME12")
        assert msg.channel == 1
        assert msg.name == "NAME12"

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ChannelNamePart1Message()
        msg.channel = 1
        msg.name = "NAME12"
        assert msg.data_to_binary() == bytes([0xF0, 0x01]) + b"NAME12"


class TestChannelNamePart1Message2:
    """Tests for ChannelNamePart1Message2 (integer channel)."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart1Message2()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05]) + b"ABCDEF")
        assert msg.channel == 5
        assert msg.name == "ABCDEF"


class TestChannelNamePart1Message3:
    """Tests for ChannelNamePart1Message3 (VMB1BL/VMB2BL)."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart1Message3()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x02]) + b"ABCD")
        assert msg.channel == 1
        assert msg.name == "ABCD"


class TestChannelNamePart2Message:
    """Tests for ChannelNamePart2Message."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart2Message()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]) + b"NAME12")
        assert msg.channel == 1
        assert msg.name == "NAME12"

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ChannelNamePart2Message()
        msg.channel = 1
        msg.name = "NAME12"
        assert msg.data_to_binary() == bytes([0xF1, 0x01]) + b"NAME12"


class TestChannelNamePart2Message2:
    """Tests for ChannelNamePart2Message2."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart2Message2()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05]) + b"ABCDEF")
        assert msg.channel == 5
        assert msg.name == "ABCDEF"


class TestChannelNamePart2Message3:
    """Tests for ChannelNamePart2Message3."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart2Message3()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x02]) + b"ABCD")
        assert msg.channel == 1
        assert msg.name == "ABCD"


class TestChannelNamePart3Message:
    """Tests for ChannelNamePart3Message."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart3Message()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]) + b"ABCD")
        assert msg.channel == 1
        assert msg.name == "ABCD"

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ChannelNamePart3Message()
        msg.channel = 1
        msg.name = "ABCD"
        assert msg.data_to_binary() == bytes([0xF2, 0x01]) + b"ABCD"


class TestChannelNamePart3Message2:
    """Tests for ChannelNamePart3Message2."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart3Message2()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05]) + b"ABCD")
        assert msg.channel == 5
        assert msg.name == "ABCD"


class TestChannelNamePart3Message3:
    """Tests for ChannelNamePart3Message3."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNamePart3Message3()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x02]) + b"ABCD")
        assert msg.channel == 1
        assert msg.name == "ABCD"


class TestMemoTextMessage:
    """Tests for MemoTextMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = MemoTextMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x00, 0x03]) + b"Hi")
        assert msg.start == 3
        assert msg.name == "Hi"

    def test_data_to_binary_pads_to_five(self):
        """Test Data to binary pads to five."""
        msg = MemoTextMessage()
        msg.start = 3
        msg.memo_text = "Hi"
        assert msg.data_to_binary() == bytes([0xAC, 0x00, 0x03]) + b"Hi\x00\x00\x00"
