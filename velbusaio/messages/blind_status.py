"""Blind Status message.

:author: Tom Dupré <gitd8400@gmail.com>
"""

from __future__ import annotations

import json

from velbusaio.command_registry import register
from velbusaio.message import Message
from velbusaio.message_fields import (
    BlindChannelField,
    BlindStatusField,
    ByteField,
    ChannelField,
    DeclarativeMessage,
)

COMMAND_CODE = 0xEC
DSTATUS = {0: "off", 1: "up", 2: "down"}


@register(COMMAND_CODE)
class BlindStatusNgMessage(DeclarativeMessage):
    """Blind Status NG message."""

    _command_code = COMMAND_CODE
    _data_length = 7
    _generates_data_to_binary = False

    channel = ChannelField(0)
    timeout = ByteField(1)
    status = ByteField(2)
    position = ByteField(4, default=None)

    def to_json(self):
        """To json."""
        json_dict = self.to_json_basic()
        json_dict["channel"] = self.channel
        json_dict["timeout"] = self.timeout
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


@register(COMMAND_CODE)
class BlindStatusNg20Message(BlindStatusNgMessage):
    """Blind Status NG20 message."""

    def __init__(self, address=None):
        """Initialize BlindStatusNg20Message class."""
        Message.__init__(self)
        self.channel = (1, 2)
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
        self.channel = (1, 2)
        channel1_status = data[0] & 0x03
        channel2_status = (data[0] >> 4) & 0x03
        self.status = (channel1_status, channel2_status)
        self.position = (data[1], data[2])

    def to_json(self):
        """To json."""
        json_dict = self.to_json_basic()
        json_dict["channel"] = self.channel
        json_dict["timeout"] = self.timeout
        json_dict["position"] = self.position
        json_dict["status"] = (DSTATUS[self.status[0]], DSTATUS[self.status[1]])
        return json.dumps(json_dict)


@register(COMMAND_CODE)
class BlindStatusMessage(DeclarativeMessage):
    """Blind Status message."""

    _command_code = COMMAND_CODE
    _data_length = 7
    _generates_data_to_binary = False

    channel = BlindChannelField(0)
    timeout = ByteField(1)
    status = BlindStatusField(2)

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
