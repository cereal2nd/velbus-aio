"""Module Status Request Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message
from velbusaio.message_fields import (
    BitField,
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
class ModuleStatusGP4PirMessage(Message):
    """Module Status GP4 PIR Message."""

    def __init__(self, address=None):
        """Initialize Module Status GP4 PIR Message object."""
        Message.__init__(self)
        # in data[0]
        self.closed = []
        self.enabled = []  # only 4 bits
        # self.normal = []
        self.locked = []
        self.programenabled = []
        self.selected_program = 0
        self.selected_program_str = PROGRAM_SELECTION[self.selected_program]

        # in data[1] and data[2]
        self.light_value: int = 0
        # in data[5]
        self.selected_program = 0
        self.selected_program_str = PROGRAM_SELECTION[self.selected_program]
        # in data[6]
        self.light_value_send_interval = 0

    def populate(self, priority, address, rtr, data):
        """Populate the message from binary data."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.closed = self.byte_to_channels(data[0])
        self.enabled = self.byte_to_channels(data[1])
        self.locked = self.byte_to_channels(data[3])
        self.light_value = ((data[1] & 0x30) << 4) + data[2]
        self.programenabled = self.byte_to_channels(data[4])
        self.selected_program = data[5] & 0x03
        self.selected_program_str = PROGRAM_SELECTION[self.selected_program]
        self.light_value_send_interval = data[6]

    def data_to_binary(self):
        """:return: bytes"""
        raise NotImplementedError
