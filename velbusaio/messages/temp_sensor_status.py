"""TempSensorStatus message implementation.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

import json

from velbusaio.command_registry import register
from velbusaio.message_fields import (
    BitField,
    ComputedField,
    DeclarativeMessage,
    Field,
    Int16Field,
)

COMMAND_CODE = 0xEA
DSTATUS = {0: "run", 2: "manual", 4: "sleep", 6: "disable"}
DMODE = {0: "safe", 16: "night", 32: "day", 64: "comfort"}


@register(COMMAND_CODE)
class TempSensorStatusMessage(DeclarativeMessage):
    """TempSensorStatus message class."""

    _command_code = COMMAND_CODE
    _priority = None
    _data_length = 7
    _generates_data_to_binary = False

    local_control = BitField(0, 0x01, default=0, serializable=False)
    status_mode = BitField(0, 0x06, default=0, serializable=False)
    status_str = ComputedField(
        parser=lambda data: DSTATUS[data[0] & 0x06],
        default="run",
        serializable=False,
    )
    auto_send = BitField(0, 0x08, default=0, serializable=False)
    mode = BitField(0, 0x70, default=0, serializable=False)
    mode_str = ComputedField(
        parser=lambda data: DMODE[data[0] & 0x70],
        default="safe",
        serializable=False,
    )
    cool_mode = BitField(0, 0x80, default=False, as_bool=True, serializable=False)
    heater = BitField(2, 0x01, default=False, as_bool=True, serializable=False)
    boost = BitField(2, 0x02, default=False, as_bool=True, serializable=False)
    pump = BitField(2, 0x04, default=False, as_bool=True, serializable=False)
    cooler = BitField(2, 0x08, default=False, as_bool=True, serializable=False)
    alarm1 = BitField(2, 0x10, default=False, as_bool=True, serializable=False)
    alarm2 = BitField(2, 0x20, default=False, as_bool=True, serializable=False)
    alarm3 = BitField(2, 0x40, default=False, as_bool=True, serializable=False)
    alarm4 = BitField(2, 0x80, default=False, as_bool=True, serializable=False)
    current_temp = Field(
        byte_index=3,
        default=None,
        parser=lambda data: data[3] / 2,
        serializable=False,
    )
    target_temp = Field(
        byte_index=4,
        default=None,
        parser=lambda data: data[4] / 2,
        serializable=False,
    )
    sleep_timer = Int16Field(5, default=None, serializable=False)

    def getCurTemp(self):
        """Get current temperature."""
        return self.current_temp

    def to_json(self):
        """:return: str"""
        json_dict = self.to_json_basic()
        json_dict["local_control"] = self.local_control
        json_dict["status_mode"] = DSTATUS[self.status_mode]
        json_dict["auto_send"] = self.auto_send
        json_dict["mode"] = DMODE[self.mode]
        json_dict["cool_mode"] = self.cool_mode
        json_dict["heater"] = self.heater
        json_dict["boost"] = self.boost
        json_dict["pump"] = self.pump
        json_dict["cooler"] = self.cooler
        json_dict["alarm1"] = self.alarm1
        json_dict["alarm2"] = self.alarm2
        json_dict["alarm3"] = self.alarm3
        json_dict["alarm4"] = self.alarm4
        json_dict["current_temp"] = self.current_temp
        json_dict["target_temp"] = self.target_temp
        json_dict["sleep_timer"] = self.sleep_timer
        return json.dumps(json_dict)
