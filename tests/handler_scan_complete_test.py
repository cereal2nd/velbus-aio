"""Tests for full-bus scan completion callbacks and stale module pruning."""

from unittest.mock import AsyncMock

import pytest

from velbusaio.controller import Velbus
from velbusaio.handler import PacketHandler
from velbusaio.module import Module

VMBGP4 = 0x20


@pytest.mark.asyncio
async def test_scan_complete_callback_registration():
    velbus = Velbus("tcp://127.0.0.1:1")
    callback = AsyncMock()
    velbus.add_scan_complete_callback(callback)
    await velbus.notify_scan_complete({1, 42})
    callback.assert_awaited_once_with({1, 42})
    velbus.remove_scan_complete_callback(callback)
    callback.reset_mock()
    await velbus.notify_scan_complete({2})
    callback.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_stale_module_drops_cache_and_submodules(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    velbus = Velbus("tcp://127.0.0.1:1", cache_dir=str(cache_dir))
    parent = Module(0x28, VMBGP4, cache_dir=str(cache_dir))
    velbus._modules[0x28] = parent
    velbus._submodules = [0x02]
    parent._sub_address = {3: 0x02}
    (cache_dir / "40.json").write_text("{}")

    await velbus.remove_stale_module(0x28)

    assert 0x28 not in velbus._modules
    assert 0x02 not in velbus._submodules
    assert not (cache_dir / "40.json").exists()


@pytest.mark.asyncio
async def test_finalize_full_scan_prunes_and_notifies(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    velbus = Velbus("tcp://127.0.0.1:1", cache_dir=str(cache_dir))
    velbus._modules[3] = Module(3, VMBGP4, cache_dir=str(cache_dir))
    (cache_dir / "3.json").write_text("{}")
    handler = PacketHandler(velbus)
    scan_done = AsyncMock()
    velbus.add_scan_complete_callback(scan_done)

    await handler._finalize_full_scan(1, 5, {1: None, 2: object(), 3: None, 4: None})

    assert 3 not in velbus._modules
    assert not (cache_dir / "3.json").exists()
    scan_done.assert_awaited_once_with({2})


@pytest.mark.asyncio
async def test_finalize_full_scan_skipped_for_one_address_mode():
    velbus = Velbus("tcp://127.0.0.1:1", one_address=5)
    velbus._modules[99] = Module(99, VMBGP4)
    handler = PacketHandler(velbus, one_address=5)
    scan_done = AsyncMock()
    velbus.add_scan_complete_callback(scan_done)

    await handler._finalize_full_scan(5, 6, {5: object()})

    assert 99 in velbus._modules
    scan_done.assert_not_awaited()
