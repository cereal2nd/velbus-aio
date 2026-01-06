"""Dali Device Settings message.

:author: Niels Laukens
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Self

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xE8


@register(COMMAND_CODE, ["VMBDALI", "VMBDALI-20"])
class DaliDeviceSettingMsg(Message):
    """Dali Device Setting message."""

    def __init__(self, address: int | None = None):
        """Initialize Dali Device Setting message."""
        super().__init__()
        self.set_defaults(address)
        self.channel: int = 0

    def populate(self, priority, address: int, rtr: int, data: bytes) -> None:
        """Populate message attributes."""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)

        self.needs_data(data, 2)
        self.channel = data[0]
        message_subtype = data[1]
        self.data: bytes | DaliDeviceSettingSubMessage = data[2:]
        try:
            decode_class = DaliDeviceSetting(message_subtype).decode_class
            if decode_class is not None:
                self.data = decode_class.from_data(self.data)
        except (ValueError, KeyError):
            # Unknown subtype or error while decoding; leave as bytes
            pass

    def to_json_basic(self):
        """Generate a basic JSON representation of the message."""
        me = {
            "name": str(self.__class__.__name__),
            "priority": self.priority,
            "rtr": self.rtr,
            "channel": self.channel,
        }
        if isinstance(self.data, DaliDeviceSettingSubMessage):
            me["data"] = self.data.to_json_basic()
        else:
            me["data"] = self.data.hex()
        return me


class DaliDeviceSettingSubMessage:
    """Abstract base class."""

    @classmethod
    def from_data(cls, data: bytes) -> DaliDeviceSettingSubMessage:
        """From data factory method."""
        raise NotImplementedError

    def to_data(self) -> bytes:
        """To data method."""
        raise NotImplementedError

    def to_json_basic(self):
        """To JSON basic representation."""
        raise NotImplementedError


class DeviceType(enum.Enum):
    """Dali Device Type enum."""

    FluorecentLamp = 0
    EmergencyLamp = 1
    DischargeLamp = 2
    LowVoltageLamp = 3
    Dimmer = 4
    ConversionToDc = 5
    LedModule = 6
    Relay = 7
    ColorControl = 8
    Sequencer = 9
    DevicePresent = 254
    NoDevicePresent = 255


@dataclasses.dataclass
class DeviceTypeMsg(DaliDeviceSettingSubMessage):
    """Dali Device Type message."""

    device_type: DeviceType

    @classmethod
    def from_data(cls, data: bytes) -> DeviceTypeMsg:
        """From data method."""
        if len(data) != 1:
            raise ValueError("Expected 1 byte of data")
        return DeviceTypeMsg(device_type=DeviceType(data[0]))

    def to_data(self) -> bytes:
        """To data method."""
        return bytes([self.device_type.value])

    def to_json_basic(self):
        """To JSON basic representation."""
        return {
            "submsg_type": self.__class__.__name__,
            "device_type": self.device_type.name,
        }


@dataclasses.dataclass
class MemberOfGroupMsg(DaliDeviceSettingSubMessage):
    """Dali Member Of Group message."""

    member_of_group: list[bool]

    @classmethod
    def from_data(cls, data: bytes) -> DaliDeviceSettingSubMessage:
        """From data method."""
        if len(data) != 2:
            raise ValueError("Expected 2 bytes")
        i = int.from_bytes(data, "little")
        member_of_groups = [bool(i & (1 << group_num)) for group_num in range(16)]
        return MemberOfGroupMsg(member_of_groups)

    def to_data(self) -> bytes:
        """To data method."""
        i = 0
        for group_num, member in enumerate(self.member_of_group):
            if member:
                i += 1 << group_num
        return i.to_bytes(2, "little")

    def to_json_basic(self):
        """To JSON basic representation."""
        return {
            "member_of_groups": self.member_of_groups,
        }

    @property
    def member_of_groups(self) -> list[int]:
        """Get list of group numbers the device is member of."""
        groups = []
        for num, member in enumerate(self.member_of_group):
            if member:
                groups.append(num)
        return groups


class DaliDeviceSetting(enum.Enum):
    """Dali Device Setting enum."""

    def __new__(
        cls, value: int, decode_class: type[DaliDeviceSettingSubMessage]
    ) -> Self:
        """New method."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.decode_class = decode_class
        return obj

    Scene0Level = (0, None)
    Scene1Level = (1, None)
    Scene2Level = (2, None)
    Scene3Level = (3, None)
    Scene4Level = (4, None)
    Scene5Level = (5, None)
    Scene6Level = (6, None)
    Scene7Level = (7, None)
    Scene8Level = (8, None)
    Scene9Level = (9, None)
    Scene10Level = (10, None)
    Scene11Level = (11, None)
    Scene12Level = (12, None)
    Scene13Level = (13, None)
    Scene14Level = (14, None)
    Scene15Level = (15, None)
    PowerOnLevel = (16, None)
    SystemFailureLevel = (17, None)
    MinimumLevel = (18, None)
    MaximumLevel = (19, None)
    FadeTimeAndRate = (20, None)
    MemberOfGroup = (21, MemberOfGroupMsg)
    GroupMembers0 = (22, None)
    GroupMembers32 = (23, None)
    # currently undefined 24
    DeviceType = (25, DeviceTypeMsg)
    ActualLevel = (26, None)
