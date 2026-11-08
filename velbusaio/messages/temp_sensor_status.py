"""TempSensorStatus message implementation.

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from typing import cast

from velbusaio.command_registry import register
from velbusaio.json_labels import (
    THERMOSTAT_MODE_JSON_MAP,
    THERMOSTAT_STATUS_JSON_MAP,
    ThermostatModeLabel,
    ThermostatRunStatusLabel,
)
from velbusaio.message_fields import (
    BitField,
    ComputedField,
    DeclarativeMessage,
    Field,
    Int16Field,
)

COMMAND_CODE = 0xEA
DSTATUS = THERMOSTAT_STATUS_JSON_MAP
DMODE = THERMOSTAT_MODE_JSON_MAP


@register(COMMAND_CODE)
class TempSensorStatusMessage(DeclarativeMessage):
    """TempSensorStatus message class."""

    _command_code = COMMAND_CODE
    _priority = None
    _data_length = 7
    _generates_data_to_binary = False
    _generates_to_json = True

    local_control = BitField(0, 0x01, default=0, serializable=False)
    status_mode = BitField(0, 0x06, default=0, serializable=False, json_map=DSTATUS)
    status_str = ComputedField(
        parser=lambda data: DSTATUS[data[0] & 0x06],
        default=ThermostatRunStatusLabel.RUN,
        serializable=False,
    )
    auto_send = BitField(0, 0x08, default=0, serializable=False)
    mode = BitField(0, 0x70, default=0, serializable=False, json_map=DMODE)
    mode_str = ComputedField(
        parser=lambda data: DMODE[data[0] & 0x70],
        default=ThermostatModeLabel.SAFE,
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
        parser=lambda data: (data[3] - 256 if data[3] & 0x80 else data[3]) / 2,
        serializable=False,
    )
    target_temp = Field(
        byte_index=4,
        default=None,
        parser=lambda data: (data[4] - 256 if data[4] & 0x80 else data[4]) / 2,
        serializable=False,
    )
    sleep_timer = Int16Field(5, default=None, serializable=False)

    def getCurTemp(self) -> float | None:
        """Get current temperature."""
        return cast("float | None", self.current_temp)
