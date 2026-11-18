"""Signum Manager channel id remapping without importing :mod:`velbusaio.module`."""

from __future__ import annotations

# Signum channelId -> velbus spec channel number when they differ.
CHANNEL_REMAPS: dict[int, dict[int, int]] = {}


def remap_channel_number(module_type_code: int, channel_id: int) -> int:
    """Map a Signum channelId to the velbus spec channel number."""
    per_type = CHANNEL_REMAPS.get(module_type_code, {})
    return per_type.get(channel_id, channel_id)
