"""Regression tests for VLP sub-address parsing (issue #204)."""

import json
import logging

import pytest

from velbusaio.controller import Velbus
from velbusaio.module import Module, VmbDali, _coerce_cached_sub_address
from velbusaio.messages.module_type_request import ModuleTypeRequestMessage
from velbusaio.vlp_reader import parse_vlp_sub_address_map


VMBDALI = 0x45


def test_parse_vlp_sub_address_map_hex_slots():
    """Sub-addresses from a VLP project file are hex, numbered from 1 like the bus."""
    addr_field = "28,FF,FF,FF,FF,FF,FF,FF,02,FF"
    assert parse_vlp_sub_address_map(addr_field) == {
        1: 0xFF,
        2: 0xFF,
        3: 0xFF,
        4: 0xFF,
        5: 0xFF,
        6: 0xFF,
        7: 0xFF,
        8: 0x02,
        9: 0xFF,
    }


def test_parse_vlp_sub_address_map_primary_only():
    assert parse_vlp_sub_address_map("28") == {}


def test_coerce_cached_sub_address_hex():
    assert _coerce_cached_sub_address("FF") == 0xFF
    assert _coerce_cached_sub_address("02") == 2
    assert _coerce_cached_sub_address(2) == 2


def test_add_submodules_skips_parsed_vlp_empty_slots():
    module = Module(0x28, VMBDALI)
    velbus = Velbus.__new__(Velbus)
    velbus._submodules = []
    velbus.add_submodules(module, parse_vlp_sub_address_map("28,FF,FF,02,FF"))
    assert module._sub_address == {3: 0x02}
    assert velbus._submodules == [0x02]


class MockWriter:
    def __init__(self):
        self.messages = []

    async def __call__(self, msg):
        self.messages.append(msg)


@pytest.mark.asyncio
async def test_load_accepts_hex_sub_addresses_from_cache(tmp_path):
    """Legacy caches written with hex strings must not abort startup."""
    module = VmbDali(0x28, VMBDALI, cache_dir=str(tmp_path))
    module._log = logging.getLogger("velbus-module")
    writer = MockWriter()
    await module.initialize(writer, None)
    cfile = tmp_path / "40.json"
    cfile.write_text(
        json.dumps(
            {
                "name": "DALI",
                "channels": {},
                "sub_addresses": {
                    "0": "FF",
                    "8": "02",
                    "9": "FF",
                },
                "properties": {},
            }
        )
    )

    await module.load()

    assert module._sub_address == {8: 2}


@pytest.mark.asyncio
async def test_load_drops_cache_with_unparseable_sub_address(tmp_path):
    module = Module(0x01, 0x20, cache_dir=str(tmp_path))
    module._log = logging.getLogger("velbus-module")
    writer = MockWriter()
    await module.initialize(writer, None)
    cfile = tmp_path / "1.json"
    cfile.write_text(
        json.dumps(
            {
                "name": "x",
                "channels": {},
                "sub_addresses": {"1": "not-a-number"},
                "properties": {},
            }
        )
    )

    await module.load()

    assert not cfile.exists()
    assert any(isinstance(m, ModuleTypeRequestMessage) for m in writer.messages)
