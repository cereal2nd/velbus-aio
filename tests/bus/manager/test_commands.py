"""Tests for Signum command translation."""

from __future__ import annotations

import tempfile

import pytest

from fake_manager import FakeManager
from velbusaio.controller import Velbus
from velbusaio.messages.switch_relay_on import SwitchRelayOnMessage


@pytest.mark.asyncio
async def test_relay_on_produces_post(open_manager: FakeManager) -> None:
    cache = tempfile.mkdtemp()
    dsn = f"manager://{open_manager.host}:{open_manager.port}"
    velbus = Velbus(dsn=dsn, cache_dir=cache)
    try:
        await velbus.connect()
        await velbus.start()
        msg = SwitchRelayOnMessage(address=5)
        msg.relay_channels = [1]
        await velbus.send(msg)
        assert len(open_manager.requests) == 1
        req = open_manager.requests[0]
        assert req.method == "POST"
        assert req.path.endswith("/things/CHREL1/actions/On")
    finally:
        await velbus.stop()
