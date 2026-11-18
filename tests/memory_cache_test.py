"""Tests for EEPROM shadow cache behaviour."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from velbusaio.actions import ActionSlot, build_action_tables
from velbusaio.controller import Velbus
from velbusaio.memory import MemoryBackend
from velbusaio.messages.memory_data_block import MemoryDataBlockMessage
from velbusaio.messages.read_data_block_from_memory import (
    ReadDataBlockFromMemoryMessage,
)
from velbusaio.module import Module


class TestMemoryBackendVlpSeed:
    """Tests for seeding EEPROM cache from VLP hex dumps."""

    def test_seed_from_vlp_hex(self):
        """Test Seed from vlp hex."""
        backend = MemoryBackend(0x11, AsyncMock())
        backend.seed_from_vlp_hex("00FF12AB")
        assert backend.get_cached(0) == 0x00
        assert backend.get_cached(1) == 0xFF
        assert backend.get_cached(2) == 0x12
        assert backend.get_cached(3) == 0xAB


class TestModuleMemoryCache:
    """Tests for module-level EEPROM shadow cache."""

    @pytest.mark.asyncio
    async def test_get_channel_actions_loads_from_bus(self, tmp_path):
        """Action tables load on demand when get_channel_actions is called."""
        store = dict.fromkeys(range(0x0000, 0x0100), 0xFF)
        writer = AsyncMock()
        backend = MemoryBackend(0x11, writer, timeout=1.0)

        async def respond(msg):
            if isinstance(msg, ReadDataBlockFromMemoryMessage):
                addr = (msg.high_address << 8) | msg.low_address
                data = bytes(store.get(addr + i, 0xFF) for i in range(4))
                reply = MemoryDataBlockMessage(0x11)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = data
                backend.feed_message(reply)

        writer.side_effect = respond

        spec = {
            "actions": "relay_classic",
            "channels": {"01": {"bank": "0000"}},
            "slot_count": 4,
            "slot_size": 6,
        }
        tables = build_action_tables(backend, spec)
        module = Module(0x11, 0x16, cache_dir=str(tmp_path))
        module._memory = backend
        module._action_tables = tables

        slots = await module.get_channel_actions(1, include_empty=True)
        assert len(slots) == 4
        assert tables[1].loaded

    @pytest.mark.asyncio
    async def test_decode_from_cache_without_bus(self, tmp_path):
        """Test Decode from cache without bus."""
        writer = AsyncMock()
        backend = MemoryBackend(0x11, writer, timeout=1.0)
        spec = {
            "actions": "relay_classic",
            "channels": {"01": {"bank": "0000"}},
            "slot_count": 4,
            "slot_size": 6,
        }
        tables = build_action_tables(backend, spec)
        for addr in range(0x18):
            backend._cache[addr] = 0xFF
        module = Module(0x11, 0x16, cache_dir=str(tmp_path))
        module._memory = backend
        module._action_tables = tables

        slots = await module.get_channel_actions(1, include_empty=True)
        assert len(slots) == 4
        writer.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalidate_config_memory_cache_clears_decoded_state(self, tmp_path):
        """Test Invalidate config memory cache clears decoded state."""
        backend = MemoryBackend(0x11, AsyncMock())
        spec = {
            "actions": "relay_classic",
            "channels": {"01": {"bank": "0000"}},
            "slot_count": 2,
            "slot_size": 6,
        }
        tables = build_action_tables(backend, spec)
        module = Module(0x11, 0x16, cache_dir=str(tmp_path))
        module._memory = backend
        module._action_tables = tables
        tables[1]._slots = []
        backend._cache[0] = 0x12

        module.invalidate_config_memory_cache()
        assert tables[1]._slots is None
        assert backend.get_cached(0) is None

    @pytest.mark.asyncio
    async def test_get_actions_uses_loaded_slots_without_bus(self, tmp_path):
        """Test Get actions uses decoded shadow slots without bus access."""
        writer = AsyncMock()
        backend = MemoryBackend(0x11, writer, timeout=1.0)
        spec = {
            "actions": "relay_classic",
            "channels": {"01": {"bank": "0000"}},
            "slot_count": 2,
            "slot_size": 6,
        }
        tables = build_action_tables(backend, spec)
        tables[1]._slots = [
            ActionSlot.empty_slot(0),
            ActionSlot.empty_slot(1),
        ]
        module = Module(0x11, 0x16, cache_dir=str(tmp_path))
        module._memory = backend
        module._action_tables = tables

        slots = await module.get_channel_actions(1, include_empty=True)
        assert len(slots) == 2
        writer.assert_not_called()


class TestVelbusReconnectCache:
    """Tests for reconnect cache invalidation."""

    @pytest.mark.asyncio
    async def test_reconnect_invalidates_memory_cache(self, tmp_path):
        """Test Reconnect invalidates memory cache."""
        velbus = Velbus("", cache_dir=str(tmp_path))
        module = Module(0x11, 0x16, cache_dir=str(tmp_path))
        backend = MemoryBackend(0x11, AsyncMock())
        backend._cache[0] = 0x42
        module._memory = backend
        velbus._modules[0x11] = module
        velbus._had_modules_before_connect = True

        await velbus._on_connection_state(True)

        assert backend.get_cached(0) is None
