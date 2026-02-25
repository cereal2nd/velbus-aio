"""Blind Status message.

:author: Tom Dupré <gitd8400@gmail.com>
"""

from __future__ import annotations

import json

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xEC
DSTATUS = {0: "off", 1: "up", 2: "down"}


@register(COMMAND_CODE, ["VMB1BLE", "VMB2BLE", "VMB1BLS", "VMB2BLE-10"])
class BlindStatusNgMessage(Message):
    """Blind Status NG message."""

    def __init__(self, address=None):
        """Initialize BlindStatusNgMessage class."""
        Message.__init__(self)
        self.channel = 0
        self.timeout = 0
        self.status = 0
        self.position = None
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """Populate message fields."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        self.channel = self.byte_to_channel(data[0])
        self.timeout = data[1]  # Omzetter seconden ????
        self.status = data[2]
        self.position = data[4]  # 0..255 (0=open, 255=closed)

    def to_json(self):
        """To json."""
        json_dict = self.to_json_basic()
        json_dict["channel"] = self.channel
        json_dict["position"] = self.position
        json_dict["status"] = DSTATUS[self.status]
        return json.dumps(json_dict)

    def is_moving_up(self) -> bool:
        """Is moving up."""
        return self.status == 0x01

    def is_moving_down(self) -> bool:
        """Is moving down."""
        return self.status == 0x02

    def is_stopped(self) -> bool:
        """Is stopped."""
        return self.status == 0x00

    def data_to_binary(self):
        """To binary data."""
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte([self.channel]),
                self.timeout,
                self.status,
                self.led_status,
                self.blind_position,
                self.locked_inhibit_forced,
                self.alarm_auto_mode_selection,
            ]
        )


@register(COMMAND_CODE, ["VMB2BLE-20"])
class BlindStatusNg20Message(BlindStatusNgMessage):
    """Blind Status NG20 message."""

    def populate(self, priority, address, rtr, data):
        """Populate message fields."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)

        # Determine channel and action
        # Each message contains the position of both channels. The "stopped" message doesn't specify the channel so both channels are updated. The "moving" messages specify the channel and we can update only that channel.
        if data[0] == 0x00:
            self.channel = (1, 2)
            self.status = 0x00
            self.position = (data[1], data[2])  # 0..100 (0=open, 100=closed)
        else:
            channel = 1 if data[0] & 0x0F else 2
            self.channel = channel
            self.status = (data[0] >> ((channel - 1) * 4)) & 0x03
            self.position = data[channel]  # 0..100 (0=open, 100=closed)


@register(COMMAND_CODE, ["VMB1BL", "VMB2BL"])
class BlindStatusMessage(Message):
    """Blind Status message."""

    def __init__(self, address=None):
        """Initialize BlindStatusMessage class."""
        Message.__init__(self)
        self.channel = 0
        self.timeout = 0
        self.status = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """Populate message fields."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)
        # 00000011 = channel 1
        # 00001100 = channel 2
        # so shift 1 bit to the right + and with 03
        tmp = (data[0] >> 1) & 0x03
        self.channel = self.byte_to_channel(tmp)
        self.timeout = data[1]  # Omzetter seconden ????
        # 2 bits per channel used
        self.status = (data[2] >> ((self.channel - 1) * 2)) & 0x03

    def to_json(self):
        """To json."""
        json_dict = self.to_json_basic()
        json_dict["channel"] = self.channel
        json_dict["timeout"] = self.timeout
        json_dict["status"] = DSTATUS[self.status]
        return json.dumps(json_dict)

    def is_moving_up(self) -> bool:
        """Is moving up."""
        return self.status == 0x01

    def is_moving_down(self) -> bool:
        """Is moving down."""
        return self.status == 0x02

    def is_stopped(self) -> bool:
        """Is stopped."""
        return self.status == 0x00
