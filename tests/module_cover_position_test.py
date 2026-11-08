"""Tests for CoverPosMessage (0x1C) handling on blind modules."""

import pytest

from velbusaio.channels import Blind
from velbusaio.const import NO_RTR, PRIORITY_HIGH
from velbusaio.controller import Velbus
from velbusaio.helpers import get_cache_dir
from velbusaio.messages.cover_position import CoverPosMessage
from velbusaio.module import Module

VMB2BLE_10 = 0x4A


@pytest.mark.asyncio
async def test_cover_position_updates_blind_position() -> None:
    module_address = 1
    velbus = Velbus("")
    module = Module(module_address, VMB2BLE_10, cache_dir=get_cache_dir())
    await module.initialize(velbus.send, velbus)

    blind = Blind(
        module, 1, "Blind 1", False, True, velbus.send, module_address
    )
    module._channels[1] = blind

    msg = CoverPosMessage(module_address)
    msg.populate(PRIORITY_HIGH, module_address, NO_RTR, bytes([0x01, 75]))
    await module.on_message(msg)

    assert blind.get_position() == 75
