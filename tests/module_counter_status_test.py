"""Tests for counter status (0xBE) handling on VMB7IN."""

import pytest

from velbusaio.channels import ButtonCounter
from velbusaio.const import ENERGY_KILO_WATT_HOUR, NO_RTR, PRIORITY_LOW
from velbusaio.controller import Velbus
from velbusaio.helpers import get_cache_dir
from velbusaio.messages.counter_status import CounterStatusMessage
from velbusaio.messages.kwh_status import KwhStatusMessage
from velbusaio.module import Module

VMB7IN = 0x22


@pytest.mark.asyncio
async def test_counter_status_sets_instantaneous_power() -> None:
    module_address = 10
    velbus = Velbus("")
    module = Module(module_address, VMB7IN, cache_dir=get_cache_dir())
    await module.initialize(velbus.send, velbus)

    counter = ButtonCounter(
        module, 2, "kWh", False, True, velbus.send, module_address
    )
    counter.set_unit(ENERGY_KILO_WATT_HOUR)
    module._channels[2] = counter

    msg = CounterStatusMessage(module_address)
    msg.populate(
        PRIORITY_LOW, module_address, NO_RTR, bytes([0x05, 0, 0, 0, 100, 0, 10])
    )
    await module.on_message(msg)

    assert counter._power == round(msg.watt, 2)
    assert counter.get_counter_state() != counter.energy


@pytest.mark.asyncio
async def test_kwh_status_message_uses_same_handler() -> None:
    module_address = 11
    velbus = Velbus("")
    module = Module(module_address, VMB7IN, cache_dir=get_cache_dir())
    await module.initialize(velbus.send, velbus)

    counter = ButtonCounter(
        module, 1, "kWh", False, True, velbus.send, module_address
    )
    counter.set_unit(ENERGY_KILO_WATT_HOUR)
    module._channels[1] = counter

    msg = KwhStatusMessage(module_address)
    msg.populate(
        PRIORITY_LOW, module_address, NO_RTR, bytes([0x04, 0, 0, 0, 50, 0, 20])
    )
    await module.on_message(msg)

    assert counter._counter == 50
    assert counter._power == round(msg.watt, 2)
