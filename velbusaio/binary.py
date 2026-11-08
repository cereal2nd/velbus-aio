"""Big-endian binary helpers for Velbus payloads."""

from __future__ import annotations

from collections.abc import Sequence


def first_channel_payload(command: int, channels: Sequence[int]) -> bytes:
    """Relay -20 payload: command byte plus first channel index (0 if empty)."""
    channel = channels[0] if channels else 0
    return bytes([command, channel])


def parse_be_uint16(data: bytes, offset: int) -> int:
    """Read an unsigned 16-bit big-endian integer at ``offset``."""
    return int.from_bytes(data[offset : offset + 2], byteorder="big", signed=False)


def serialize_be_uint16(value: int) -> bytes:
    """Write an unsigned 16-bit big-endian integer."""
    return value.to_bytes(2, byteorder="big", signed=False)


def parse_dimmer_transition(data: bytes) -> int:
    """Transition time at bytes 2–3 of set/restore dimmer payloads."""
    return parse_be_uint16(data, 2)


def serialize_dimmer_transition(value: int) -> bytes:
    """Serialize dimmer transition time for set/restore dimmer payloads."""
    return serialize_be_uint16(value)
