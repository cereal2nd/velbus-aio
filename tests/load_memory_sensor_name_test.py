"""Regression tests for module memory load (home-assistant/core#188473)."""

import logging
from unittest.mock import AsyncMock

import pytest

from velbusaio.messages.read_data_block_from_memory import ReadDataBlockFromMemoryMessage
from velbusaio.module import Module

VMBMETEO = 0x31
VMBGP4PIR_2 = 0x3E


@pytest.mark.asyncio
async def test_load_memory_sensor_name_dict_requests_blocks():
    """SensorName is a per-sensor map; it must not be .split like ModuleName."""
    module = Module(0x11, VMBMETEO)
    module._log = logging.getLogger("velbus-module")
    writer = AsyncMock()
    await module.initialize(writer, None)

    await module._Module__load_memory()

    assert writer.await_count > 0
    assert all(
        isinstance(call.args[0], ReadDataBlockFromMemoryMessage)
        for call in writer.await_args_list
    )


@pytest.mark.asyncio
async def test_gp4pir_status_does_not_disable_sensor_outputs():
    """Sensor outputs must stay exposed when only push buttons have enable bits."""
    from velbusaio.channels import Sensor
    from velbusaio.const import NO_RTR, PRIORITY_LOW
    from velbusaio.messages.module_status import ModuleStatusGP4PirMessage

    module = Module(0x14, VMBGP4PIR_2)
    module._log = logging.getLogger("velbus-module")
    writer = AsyncMock()
    await module.initialize(writer, None)
    await module._load_default_channels()

    for ch in (5, 6, 7, 8):
        assert isinstance(module._channels[ch], Sensor)

    msg = ModuleStatusGP4PirMessage(module._address)
    msg.populate(
        PRIORITY_LOW,
        module._address,
        NO_RTR,
        bytes([0x00, 0x30, 0x00, 0x00, 0x00, 0x00, 0x00]),
    )
    await module.on_message(msg)

    assert module._channels[6].get_categories() == ["binary_sensor", "led"]
    assert module._channels[7].get_categories() == ["binary_sensor", "led"]
