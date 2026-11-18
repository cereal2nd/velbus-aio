"""Tests for velbusaio.bus.manager.backend.ManagerBackend."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from fake_manager import FakeManager
from velbusaio.controller import Velbus
from velbusaio.exceptions import VelbusNotSupported


@pytest.mark.asyncio
async def test_signum_connect_and_start(open_manager: FakeManager) -> None:
    cache = tempfile.mkdtemp()
    dsn = f"manager://{open_manager.host}:{open_manager.port}"
    velbus = Velbus(dsn=dsn, cache_dir=cache)
    try:
        await velbus.connect()
        await velbus.start()
        modules = velbus.get_modules()
        assert 5 in modules
        relay = modules[5].get_channels()[1]
        assert relay.get_categories() == ["switch"]
        assert relay.is_on() is False
    finally:
        await velbus.stop()


@pytest.mark.asyncio
async def test_property_status_updates_channel(open_manager: FakeManager) -> None:
    cache = tempfile.mkdtemp()
    dsn = f"manager://{open_manager.host}:{open_manager.port}"
    velbus = Velbus(dsn=dsn, cache_dir=cache)
    try:
        await velbus.connect()
        await velbus.start()
        await open_manager.broadcast(
            {
                "messageType": "propertyStatus",
                "thingId": "CHREL1",
                "data": {"On": True},
            }
        )
        await asyncio.sleep(0.2)
        relay = velbus.get_modules()[5].get_channels()[1]
        assert relay.is_on() is True
    finally:
        await velbus.stop()


@pytest.mark.asyncio
async def test_gateway_status_affects_connected(open_manager: FakeManager) -> None:
    cache = tempfile.mkdtemp()
    dsn = f"manager://{open_manager.host}:{open_manager.port}"
    velbus = Velbus(dsn=dsn, cache_dir=cache)
    try:
        await velbus.connect()
        assert velbus.connected is True
        await open_manager.broadcast(
            {
                "messageType": "gatewayStatus",
                "thingId": "GWLOCAL",
                "data": {"state": "Disconnected"},
            }
        )
        for _ in range(20):
            if not velbus.connected:
                break
            await asyncio.sleep(0.05)
        assert velbus.connected is False
    finally:
        await velbus.stop()


@pytest.mark.asyncio
async def test_gateway_created_status_does_not_drop_link(
    open_manager: FakeManager,
) -> None:
    """Stale Created state must not mark the bus down when already live."""
    cache = tempfile.mkdtemp()
    dsn = f"manager://{open_manager.host}:{open_manager.port}"
    velbus = Velbus(dsn=dsn, cache_dir=cache)
    try:
        await velbus.connect()
        await velbus.start()
        await open_manager.broadcast(
            {
                "messageType": "propertyStatus",
                "thingId": "CHREL1",
                "data": {"On": True},
            }
        )
        await asyncio.sleep(0.1)
        assert velbus.connected is True
        await open_manager.broadcast(
            {
                "messageType": "gatewayStatus",
                "thingId": "GWLOCAL",
                "data": {"state": "Created"},
            }
        )
        await asyncio.sleep(0.1)
        assert velbus.connected is True
    finally:
        await velbus.stop()


@pytest.mark.asyncio
async def test_scan_triggers_quickupdate(open_manager: FakeManager) -> None:
    cache = tempfile.mkdtemp()
    dsn = f"manager://{open_manager.host}:{open_manager.port}"
    velbus = Velbus(dsn=dsn, cache_dir=cache)
    try:
        await velbus.connect()
        await velbus.start()
        open_manager.requests.clear()
        await velbus.scan()
        action_requests = [
            r
            for r in open_manager.requests
            if r.method == "POST" and "/actions/" in r.path
        ]
        assert len(action_requests) == 1
        assert action_requests[0].path.endswith("/actions/Quickupdate")
        assert action_requests[0].body == {"Quickupdate": {"input": {}}}
    finally:
        await velbus.stop()


@pytest.mark.asyncio
async def test_sync_clock_not_supported(open_manager: FakeManager) -> None:
    cache = tempfile.mkdtemp()
    dsn = f"manager://{open_manager.host}:{open_manager.port}"
    velbus = Velbus(dsn=dsn, cache_dir=cache)
    try:
        await velbus.connect()
        with pytest.raises(VelbusNotSupported):
            await velbus.sync_clock()
    finally:
        await velbus.stop()
