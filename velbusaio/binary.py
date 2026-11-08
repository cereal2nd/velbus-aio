"""Big-endian binary helpers for Velbus payloads.

``parse_be_uint16`` and ``serialize_be_uint16`` are the canonical unsigned
big-endian uint16 codec; :class:`~velbusaio.message_fields.Int16Field` delegates
to them for wire parse/serialize.
"""

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
