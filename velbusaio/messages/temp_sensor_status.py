""":author: Maikel Punie <maikel.punie@gmail.com>"""

from __future__ import annotations

import json

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xEA
DSTATUS = {0: "run", 2: "manual", 4: "sleep", 6: "disable"}
DMODE = {0: "safe", 16: "night", 32: "day", 64: "comfort"}


@register(COMMAND_CODE)
class TempSensorStatusMessage(Message):
    """send by: VMBGPOD
    received by:
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.local_control = 0  # 0=unlocked, 1 =locked
        self.status_mode = 0  # DSTATUS
        self.status_str = "run"
        self.auto_send = 0  # 0=disabled
        self.mode = 0  # DMODE
        self.mode_str = "safe"
        self.cool_mode = False
        self.heater = False
        self.boost = False
        self.pump = False
        self.cooler = False
        self.alarm1 = False
        self.alarm2 = False
        self.alarm3 = False
        self.alarm4 = False
        self.current_temp = None
        self.target_temp = None
        self.sleep_timer = None

    def getCurTemp(self):
        return self.current_temp

    def populate(self, priority, address, rtr, data):
        """-DB1    last bit        = local_control
        -DB1    bit 2+3         = status_mode
        -DB1    bit 4           = auto send
        -DB1    bit 5+6+7       = mode
        -DB1    bit 8           = cool/heat
        -DB2                    = program (not used)
        -DB3    last bit        = heater
        -DB3    bit 2           = boost
        -DB3    bit 3           = pump
        -DB3    bit 4           = cooler
        -DB4    bit 5           = alarm 1
        -DB4    bit 6           = alarm 2
        -DB4    bit 7           = alarm 3
        -DB4    bit 8           = alarm 4
        -DB5    current temp    = current temp
        -DB6    target temp     = target temp
        -DB7-8  sleep timer     = 0=off >0=x min
        :return: None
        """
        self.needs_no_rtr(rtr)
        self.needs_data(data, 7)
        self.set_attributes(priority, address, rtr)

        self.local_control = data[0] & 0x01
        self.status_mode = data[0] & 0x06
        self.status_str = DSTATUS[self.status_mode]
        self.auto_send = data[0] & 0x08
        self.mode = data[0] & 0x70
        self.mode_str = DMODE[self.mode]
        self.cool_mode = (data[0] & 0x80) == 0x80

        self.heater = (data[2] & 0x01) == 0x01
        self.boost = (data[2] & 0x02) == 0x02
        self.pump = (data[2] & 0x04) == 0x04
        self.cooler = (data[2] & 0x08) == 0x08
        self.alarm1 = (data[2] & 0x10) == 0x10
        self.alarm2 = (data[2] & 0x20) == 0x20
        self.alarm3 = (data[2] & 0x40) == 0x40
        self.alarm4 = (data[2] & 0x80) == 0x80

        self.current_temp = data[3] / 2
        self.target_temp = data[4] / 2

        self.sleep_timer = (data[5] << 8) + data[6]

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
