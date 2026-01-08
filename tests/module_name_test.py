import logging

import pytest

from velbusaio.messages.memory_data_block import MemoryDataBlockMessage
from velbusaio.module import Module


class MockWriter:
    async def __call__(self, data):
        pass


class MockController:
    """Mock controller for testing."""

    def connected(self):
        return True

    def _add_on_connext_callback(self, callback):
        pass

    def _remove_on_connect_callback(self, callback):
        pass

    def _add_on_disconnect_callback(self, callback):
        pass

    def _remove_on_disconnect_callback(self, callback):
        pass


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

    # Prepare memory with 16 bytes initialized to 0xFF
    memory_bytes = [0xFF] * 16
    for i, c in enumerate(name):
        memory_bytes[i] = ord(c)

    # Build memory in 4-byte blocks
    memory = {}
    for i in range(0, 16, 4):
        memory[0xF0 + i] = memory_bytes[i:i + 4]

    m = Module(module_address, module_type)
    m._use_cache = False
    await m.initialize(MockWriter(), MockController())
    m._log = logging.getLogger("velbus-module")

    for addr, data in memory.items():
        msg = MemoryDataBlockMessage()
        msg.high_address = addr >> 8
        msg.low_address = addr & 0xFF
        msg.data = data
        await m._process_memory_data_block_message(msg)

    assert m.get_name() == name
