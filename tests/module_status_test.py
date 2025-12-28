"""
This test checks if with an incoming module_status message the selected program
is correctly stored into the module.
"""

import pathlib
from unittest.mock import MagicMock

import pytest

from velbusaio.channels import Channel, LightSensor, SelectedProgram
from velbusaio.const import (
    CHANNEL_LIGHT_VALUE,
    CHANNEL_SELECTED_PROGRAM,
    NO_RTR,
    PRIORITY_LOW,
)
from velbusaio.controller import Velbus
from velbusaio.helpers import get_cache_dir
from velbusaio.messages.module_status import (
    PROGRAM_SELECTION,
    ModuleStatusGP4PirMessage,
    ModuleStatusMessage2,
    ModuleStatusPirMessage,
)
from velbusaio.module import Module

# some modules to test
VMBGP4 = 0x20
VMBGPOD = 0x28
VMBPIRM = 0x2A
VMBGP4PIR = 0x2D
VMBGPOD_2 = 0x3D
VMBGP4PIR_2 = 0x3E


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "module_type",
    [
        VMBGP4,
        VMBGPOD,
        VMBGPOD_2,
        VMBGP4PIR,
        VMBGP4PIR_2,
        VMBPIRM,
    ],
)
async def test_module_status_selected_program(module_type):
    module_address = 1
    cache_dir = get_cache_dir()
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)

    velbus = MagicMock()
    m = Module(
        module_address,
        module_type,
        cache_dir=get_cache_dir(),
    )
    velbus = Velbus("")  # Dummy connection
    await m.initialize(velbus.send, velbus)

    # load the module with dummy channels
    for chan in range(1, 9):
        m._channels[chan] = Channel(None, None, None, False, False, None, None)
    m._channels[CHANNEL_LIGHT_VALUE] = LightSensor(
        None, None, None, False, False, None, None
    )
    m._channels[CHANNEL_SELECTED_PROGRAM] = SelectedProgram(
        m, None, None, False, False, velbus.send, None
    )

    messages_to_test = [
        ModuleStatusMessage2,
        ModuleStatusGP4PirMessage,
        ModuleStatusPirMessage,
    ]

    # test all message variants that have the selected_program variable
    for message in messages_to_test:
        msg = message(module_address)

        # test all possible program selections
        for program in PROGRAM_SELECTION.keys():
            msg.selected_program = program
            msg.selected_program_str = PROGRAM_SELECTION[program]
            await m.on_message(msg)
            assert (
                m._channels[CHANNEL_SELECTED_PROGRAM].get_selected_program()
                == PROGRAM_SELECTION[program]
            )

            # Send the select_program message and check if the binary data is ok
            await m._channels[CHANNEL_SELECTED_PROGRAM].set_selected_program(
                PROGRAM_SELECTION[program]
            )
            msg_info = await velbus._protocol._send_queue.get()
            assert msg_info.data[1] == program

    # test GP4PIR lightvalue
    msg = ModuleStatusGP4PirMessage(module_address)
    light_values = [0, 100, 1023]
    for light_value in light_values:
        databyte1 = (light_value & 0x300) >> 4
        databyte2 = light_value & 0xFF
        msg.populate(
            PRIORITY_LOW,
            module_address,
            NO_RTR,
            [0x00, databyte1, databyte2, 0x00, 0x00, 0x00, 0x00],
        )
        await m.on_message(msg)
        assert m._channels[CHANNEL_LIGHT_VALUE].get_state() == light_value
