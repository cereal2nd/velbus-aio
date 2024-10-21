"""
This test checks if with an incoming temp_sensor_status message the thermostat operating mode and
sleep_timer values are correctly stored into the module's temperature channel.
"""

import pathlib
from unittest.mock import MagicMock

import pytest

from velbusaio.channels import Temperature
from velbusaio.controller import Velbus
from velbusaio.handler import PacketHandler
from velbusaio.helpers import get_cache_dir
from velbusaio.messages.temp_sensor_status import DSTATUS, TempSensorStatusMessage
from velbusaio.module import Module


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode, sleep_timer",
    [
        (0, 40),
        (2, 0xFFFF),
        (4, 500),
        (6, 0),
    ],
)
async def test_thermostat_operating_mode(mode, sleep_timer):
    module_address = 1
    module_type = 0x28  # VMBGPOD
    cache_dir = get_cache_dir()
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)

    velbus = MagicMock()
    ph = PacketHandler(velbus)
    await ph.read_protocol_data()

    m = Module(
        module_address,
        module_type,
        ph.pdata["ModuleTypes"][f"{module_type:02X}"],
        cache_dir=get_cache_dir(),
    )
    velbus = Velbus("")  # Dummy connection
    m.initialize(velbus.send)
    chan = m._translate_channel_name(m._data["TemperatureChannel"])
    m._channels[chan] = Temperature(m, chan, None, False, velbus.send, None)

    msg = TempSensorStatusMessage(module_address)
    msg.status_str = DSTATUS[mode]
    msg.sleep_timer = sleep_timer
    msg.current_temp = 0
    await m.on_message(msg)

    assert m._channels[chan].get_climate_mode() == DSTATUS[mode]
    assert m._channels[chan]._sleep_timer == sleep_timer

    await m._channels[chan].set_climate_mode(DSTATUS[mode])
    msg_info = await velbus._protocol._send_queue.get()
    check_sleep_timer = (msg_info.data[1] << 8) + msg_info.data[2]
    if DSTATUS[mode] == "run":
        sleep = 0x0
    elif DSTATUS[mode] == "manual":
        sleep = 0xFFFF
    elif DSTATUS[mode] == "sleep":
        sleep = sleep_timer
    else:
        sleep = 0x0

    assert check_sleep_timer == sleep
