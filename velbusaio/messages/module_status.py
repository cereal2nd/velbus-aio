"""Module Status Request Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xED

PROGRAM_SELECTION = {0: "none", 1: "summer", 2: "winter", 3: "holiday"}


@register(COMMAND_CODE)
class ModuleStatusMessage(Message):
    """Module Status Message."""

    def __init__(self, address=None):
        """Initialize Module Status Message object."""
        Message.__init__(self)
        self.closed = []
        self.led_on = []
        self.led_slow_blinking = []
        self.led_fast_blinking = []
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 4)
        self.set_attributes(priority, address, rtr)
        self.closed = self.byte_to_channels(data[0])
        self.led_on = self.byte_to_channels(data[1])
        self.led_slow_blinking = self.byte_to_channels(data[2])
        self.led_fast_blinking = self.byte_to_channels(data[3])

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte(self.closed),
                self.channels_to_byte(self.led_on),
                self.channels_to_byte(self.led_slow_blinking),
                self.channels_to_byte(self.led_fast_blinking),
            ]
        )


@register(
    COMMAND_CODE,
    [
        "VMB8PBU",
        "VMB6PBN",
        "VMB2PBN",
        "VMB6PBB",
        "VMBGP1",
        "VMBEL1",
        "VMBGP1-2",
        "VMBGP2",
        "VMBEL2",
        "VMBGP2-2",
        "VMBGP4",
        "VMBEL4",
        "VMBGP4-2",
        "VMBGPO",
        "VMBGPOD",
        "VMBGPOD-2",
        "VMBELO",
        "VMB7IN",
        "VMB6PB-20",
        "VMBEL1-20",
        "VMBEL2-20",
        "VMBEL4-20",
        "VMBELO-20",
        "VMBGP1-20",
        "VMBGP2-20",
        "VMBGP4-20",
        "VMBGPO-20",
        "VMBEL4PIR-20",
        "VMBGP4PIR-20",
        "VMBPSUMNGR-20",
        "VMB8IN-20",
    ],
)
class ModuleStatusMessage2(Message):
    """Module Status Message for specific modules."""

    def __init__(self, address=None):
        """Initialize Module Status Message object."""
        Message.__init__(self)
        self.closed = []
        self.enabled = []
        self.normal = []
        self.locked = []
        self.programenabled = []
        self.selected_program = 0
        self.selected_program_str = PROGRAM_SELECTION[self.selected_program]

    def populate(self, priority, address, rtr, data):
        """Populate the message from binary data."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 6)
        self.set_attributes(priority, address, rtr)
        self.closed = self.byte_to_channels(data[0])
        self.enabled = self.byte_to_channels(data[1])
        self.normal = self.byte_to_channels(data[2])
        self.locked = self.byte_to_channels(data[3])
        self.programenabled = self.byte_to_channels(data[4])
        self.selected_program = data[5] & 0x03
        self.selected_program_str = PROGRAM_SELECTION[self.selected_program]

    def data_to_binary(self):
        """:return: bytes"""
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte(self.closed),
                self.channels_to_byte(self.enabled),
                self.channels_to_byte(self.normal),
                self.channels_to_byte(self.locked),
            ]
        )


@register(COMMAND_CODE, ["VMBPIRO", "VMBPIRM", "VMBPIRC", "VMBELPIR"])
class ModuleStatusPirMessage(Message):
    """Module Status PIR Message."""

    def __init__(self, address=None):
        """Initialize Module Status PIR Message object."""
        Message.__init__(self)
        # in data[0]
        self.dark: bool = False  # bit 1
        self.light: bool = False  # bit 2
        self.motion1: bool = False  # bit 3
        self.light_motion1: bool = False  # bit 4
        self.motion2: bool = False  # bit 5
        self.light_motion2: bool = False  # bit 6
        self.low_temp_alarm: bool = False  # bit 7
        self.high_temp_alarm: bool = False  # bit 8
        # in data[1] and data[2]
        self.light_value: int = 0
        # in data[5]
        self.selected_program = 0
        self.selected_program_str = PROGRAM_SELECTION[self.selected_program]

    def populate(self, priority, address, rtr, data):
        """Populate the message from binary data."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.dark = bool(data[0] & (1 << 0))
        self.light = bool(data[0] & (1 << 1))
        self.motion1 = bool(data[0] & (1 << 2))
        self.light_motion1 = bool(data[0] & (1 << 3))
        self.motion2 = bool(data[0] & (1 << 4))
        self.light_motion2 = bool(data[0] & (1 << 5))
        self.low_temp_alarm = bool(data[0] & (1 << 6))
        self.high_temp_alarm = bool(data[0] & (1 << 7))
        self.light_value = (data[1] << 8) + data[2]
        self.selected_program = data[5] & 0x03
        self.selected_program_str = PROGRAM_SELECTION[self.selected_program]

    def data_to_binary(self):
        """:return: bytes"""
        raise NotImplementedError


@register(COMMAND_CODE, ["VMBGP4PIR", "VMBGP4PIR-2"])
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
