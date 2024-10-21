from unittest.mock import MagicMock

import pytest

from velbusaio.handler import PacketHandler
from velbusaio.helpers import h2
from velbusaio.module import Module, VmbDali


class MockWriter:
    async def __call__(self, data):
        pass


@pytest.mark.asyncio
async def test_vmbdali_loads_and_has_channels():
    ph = PacketHandler(None)
    await ph.read_protocol_data()

    module_address = 0x12
    dali_type = 69
    module = VmbDali(
        module_address,
        dali_type,
        ph.pdata["ModuleTypes"][h2(dali_type)],
    )
    writer = MockWriter()
    module.initialize(writer)

    await module.load()

    assert len(module._channels) > 0
