"""Regression test for thermostat output channel synchronization.

An incoming ``TempSensorStatusMessage`` carries the on/off state of the
thermostat output channels (heater, boost, pump, cooler and the 4 alarms).
These have to be reflected onto the corresponding ``ThermostatChannel``
channels so the Home Assistant binary sensors stay in sync with Velbus.

The spec channel names differ between module generations: older modules use
short names ("Boost", "Alarm 1") while the "-20" variants use long names
("Boost heater/cooler", "Temperature alarm 1"). Both must be handled.
"""

import logging
import pathlib

import pytest

from velbusaio.const import NO_RTR, PRIORITY_LOW
from velbusaio.controller import Velbus
from velbusaio.helpers import get_cache_dir
from velbusaio.messages.temp_sensor_status import TempSensorStatusMessage
from velbusaio.module import Module

VMBEL1 = 0x34  # short thermostat channel names ("Boost", "Alarm 1")
VMBGP1_20 = 0x54  # long thermostat channel names ("Boost heater/cooler", ...)

# Thermostat output channels are always channels 10..17 in these specs.
# byte index 2 of the message holds their bitmask.
HEATER, BOOST, PUMP, COOLER = 10, 11, 12, 13
ALARM1, ALARM2, ALARM3, ALARM4 = 14, 15, 16, 17


@pytest.mark.asyncio
@pytest.mark.parametrize("module_type", [VMBEL1, VMBGP1_20])
async def test_thermostat_output_channels_sync(module_type):
    module_address = 1
    pathlib.Path(get_cache_dir()).mkdir(parents=True, exist_ok=True)

    velbus = Velbus("")  # Dummy connection
    m = Module(module_address, module_type, cache_dir=get_cache_dir())
    await m.initialize(velbus.send, velbus)
    m._log = logging.getLogger("velbus-module")
    await m._load_default_channels()

    # data[2] bitmask: heater=0x01, boost=0x02, pump=0x04, cooler=0x08,
    # alarm1=0x10, alarm2=0x20, alarm3=0x40, alarm4=0x80.
    # Turn on boost, alarm1 and alarm3.
    bitmask = 0x02 | 0x10 | 0x40
    data = bytes([0x00, 0x00, bitmask, 0x00, 0x00, 0x00, 0x00])
    msg = TempSensorStatusMessage(module_address)
    msg.populate(PRIORITY_LOW, module_address, NO_RTR, data)

    await m.on_message(msg)

    expected = {
        HEATER: False,
        BOOST: True,
        PUMP: False,
        COOLER: False,
        ALARM1: True,
        ALARM2: False,
        ALARM3: True,
        ALARM4: False,
    }
    for channel_num, is_closed in expected.items():
        assert m._channels[channel_num].is_closed() is is_closed, (
            f"channel {channel_num} closed state out of sync"
        )
