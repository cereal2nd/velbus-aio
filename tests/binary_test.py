"""Tests for velbusaio.binary helpers."""

from velbusaio.binary import parse_be_uint16, serialize_be_uint16


class TestBeUint16:
    """Unsigned big-endian 16-bit codec."""

    def test_parse_and_serialize(self) -> None:
        assert parse_be_uint16(bytes([0x12, 0x34]), 0) == 0x1234
        assert parse_be_uint16(bytes([0x00, 0x05]), 0) == 5
        assert serialize_be_uint16(0x1234) == bytes([0x12, 0x34])
        assert serialize_be_uint16(5) == bytes([0x00, 0x05])

    def test_dimmer_transition_offset(self) -> None:
        """Set/restore dimmer payloads put transition time at data[2:4]."""
        payload = bytes([0x01, 100, 0x00, 0x05])
        assert parse_be_uint16(payload, 2) == 5
        assert serialize_be_uint16(0x00FF) == bytes([0x00, 0xFF])
