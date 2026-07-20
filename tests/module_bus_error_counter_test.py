"""This test checks that an incoming bus error counter message is stored into the
bus error counter properties of the module.
"""

import pathlib

import pytest

from velbusaio.controller import Velbus
from velbusaio.helpers import get_cache_dir
from velbusaio.messages.bus_error_counter_status import BusErrorCounterStatusMessage
from velbusaio.module import Module
from velbusaio.properties import BusErrorOff, BusErrorRx, BusErrorTx

VMBGPOD = 0x28

# distinct values, so a mix-up between the three counters is caught as well
TRANSMIT_ERRORS = 11
RECEIVE_ERRORS = 22
BUS_OFF_COUNT = 33


@pytest.mark.asyncio
async def test_bus_error_counters_are_updated():
    cache_dir = get_cache_dir()
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)

    m = Module(1, VMBGPOD, cache_dir=cache_dir)
    velbus = Velbus("")  # Dummy connection
    await m.initialize(velbus.send, velbus)

    # the bus error counters are declared in module_spec/global.json, so every module
    # gets them; load them the way _load_properties() does
    m._properties["bus_error_tx"] = BusErrorTx(m, "Bus Error Transmit", velbus.send)
    m._properties["bus_error_rx"] = BusErrorRx(m, "Bus Error Receive", velbus.send)
    m._properties["bus_error_off"] = BusErrorOff(m, "Bus Error Off", velbus.send)

    msg = BusErrorCounterStatusMessage(1)
    msg.transmit_error_counter = TRANSMIT_ERRORS
    msg.receive_error_counter = RECEIVE_ERRORS
    msg.bus_off_counter = BUS_OFF_COUNT

    await m._handle_bus_error_counter(msg)

    assert m._properties["bus_error_tx"].get_state() == TRANSMIT_ERRORS
    assert m._properties["bus_error_rx"].get_state() == RECEIVE_ERRORS
    assert m._properties["bus_error_off"].get_state() == BUS_OFF_COUNT
