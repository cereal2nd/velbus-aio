"""Module Status Request Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    BitField,
    ByteField,
    ChannelsField,
    ComputedField,
    DeclarativeMessage,
    Int16Field,
)

COMMAND_CODE = 0xED

PROGRAM_SELECTION = {0: "none", 1: "summer", 2: "winter", 3: "holiday"}


@register(COMMAND_CODE)
class ModuleStatusMessage(DeclarativeMessage):
    """Module Status Message."""

    _command_code = COMMAND_CODE
    _data_length = 4

    closed = ChannelsField(0)
    led_on = ChannelsField(1)
    led_slow_blinking = ChannelsField(2)
    led_fast_blinking = ChannelsField(3)


@register(COMMAND_CODE)
class ModuleStatusMessage2(DeclarativeMessage):
    """Module Status Message for specific modules."""

    _command_code = COMMAND_CODE
    _data_length = 6

    closed = ChannelsField(0)
    enabled = ChannelsField(1)
    normal = ChannelsField(2)
    locked = ChannelsField(3)
    programenabled = ChannelsField(4)
    selected_program = BitField(5, 0x03, serializable=True)
    selected_program_str = ComputedField(
        parser=lambda data: PROGRAM_SELECTION[data[5] & 0x03],
        default=PROGRAM_SELECTION[0],
        serializable=False,
    )


@register(COMMAND_CODE)
class ModuleStatusPirMessage(DeclarativeMessage):
    """Module Status PIR Message."""

    _command_code = COMMAND_CODE
    _data_length = 7
    _generates_data_to_binary = False

    dark = BitField(0, 1 << 0, as_bool=True, default=False)  # data[0] bit 1
    light = BitField(0, 1 << 1, as_bool=True, default=False)  # data[0] bit 2
    motion1 = BitField(0, 1 << 2, as_bool=True, default=False)  # data[0] bit 3
    light_motion1 = BitField(0, 1 << 3, as_bool=True, default=False)  # data[0] bit 4
    motion2 = BitField(0, 1 << 4, as_bool=True, default=False)  # data[0] bit 5
    light_motion2 = BitField(0, 1 << 5, as_bool=True, default=False)  # data[0] bit 6
    low_temp_alarm = BitField(0, 1 << 6, as_bool=True, default=False)  # data[0] bit 7
    high_temp_alarm = BitField(0, 1 << 7, as_bool=True, default=False)  # data[0] bit 8
    light_value = Int16Field(1)  # data[1] and data[2]
    selected_program = BitField(5, 0x03)  # data[5]
    selected_program_str = ComputedField(
        parser=lambda data: PROGRAM_SELECTION[data[5] & 0x03],
        default=PROGRAM_SELECTION[0],
        serializable=False,
    )


@register(COMMAND_CODE)
class ModuleStatusGP4PirMessage(DeclarativeMessage):
    """Module Status GP4 PIR Message."""

    _command_code = COMMAND_CODE
    _data_length = 7
    _generates_data_to_binary = False

    closed = ChannelsField(0)  # data[0]
    enabled = ChannelsField(1)  # data[1], only 4 bits
    locked = ChannelsField(3)  # data[3]
    light_value = ComputedField(
        parser=lambda data: ((data[1] & 0x30) << 4) + data[2],
        default=0,
        serializable=False,
    )  # data[1] and data[2]
    programenabled = ChannelsField(4)  # data[4]
    selected_program = BitField(5, 0x03)  # data[5]
    selected_program_str = ComputedField(
        parser=lambda data: PROGRAM_SELECTION[data[5] & 0x03],
        default=PROGRAM_SELECTION[0],
        serializable=False,
    )
    light_value_send_interval = ByteField(6, default=0)  # data[6]
