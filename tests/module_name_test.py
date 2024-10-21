import logging
from unittest.mock import MagicMock

import pytest

from velbusaio.handler import PacketHandler
from velbusaio.messages.memory_data import MemoryDataMessage
from velbusaio.module import Module


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        "Temp. controller",
        "Shorter name",
    ],
)
async def test_module_name(name):
    module_address = 1
    module_type = 0x0E  # VMB1TC

    memory = {}
    for i in range(0, 16):
        memory[0xF0 + i] = 0xFF
    for i, c in enumerate(name):
        memory[0xF0 + i] = ord(c)

    velbus = MagicMock()
    ph = PacketHandler(velbus)
    await ph.read_protocol_data()
    m = Module(
        module_address, module_type, ph.pdata["ModuleTypes"][f"{module_type:02X}"]
    )
    m._log = logging.getLogger("velbus-module")

    for addr, data in memory.items():
        msg = MemoryDataMessage()
        msg.high_address = addr >> 8
        msg.low_address = addr & 0xFF
        msg.data = data
        await m._process_memory_data_message(msg)

    assert m.get_name() == name
