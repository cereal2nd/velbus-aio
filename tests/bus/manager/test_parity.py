"""Parity between Signum Manager and VLP module graphs."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from fake_manager import FakeManager
from velbusaio.controller import Velbus


def _entity_index(velbus: Velbus) -> dict[str, tuple[list[str], list[str]]]:
    result: dict[str, tuple[list[str], list[str]]] = {}
    for addr, module in velbus.get_modules().items():
        for chan in module.get_channels().values():
            key = f"{addr}-{chan.get_identifier()}"
            result[key] = (chan.get_categories(), chan.get_sensor_types())
        for prop in module.get_properties().values():
            key = f"{addr}-{prop.get_identifier()}"
            result[key] = (prop.get_categories(), [])
    return result


@pytest.mark.asyncio
async def test_vlp_signum_parity(open_manager: FakeManager) -> None:
    cache = tempfile.mkdtemp()
    vlp = Path(__file__).with_name("fixture.vlp")

    signum = Velbus(
        dsn=f"manager://{open_manager.host}:{open_manager.port}",
        cache_dir=cache,
    )
    bus = Velbus(dsn="tcp://127.0.0.1:1", cache_dir=cache, vlp_file=str(vlp))

    try:
        await signum.connect()
        await signum.start()
        await bus.start()
        signum_keys = _entity_index(signum)
        bus_keys = _entity_index(bus)
        assert set(signum_keys) == set(bus_keys)
        for key in signum_keys:
            assert signum_keys[key] == bus_keys[key]
    finally:
        await signum.stop()
        await bus.stop()
