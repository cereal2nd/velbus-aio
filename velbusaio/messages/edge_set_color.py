"""Set Edge Color message class."""

from __future__ import annotations

from enum import IntEnum

from velbusaio.command_registry import register
from velbusaio.message_fields import BitField, DeclarativeMessage, Field

COMMAND_CODE = 0xD4


class CustomColorPriority(IntEnum):
    """Custom Color Priority enum."""

    LOW_PRIORITY = 1
    MID_PRIORITY = 2
    HIGH_PRIORITY = 3


@register(COMMAND_CODE)
class SetEdgeColorMessage(DeclarativeMessage):
    """Set Edge Color message (DLC=4 variant)."""

    _command_code = COMMAND_CODE
    _priority = None

    apply_background_color = BitField(0, 0x01, as_bool=True, default=False)
    custom_color_palette = BitField(0, 0x80, as_bool=True, default=False)
    apply_to_left_edge = BitField(1, 0x01, as_bool=True, default=False)
    apply_to_top_edge = BitField(1, 0x02, as_bool=True, default=False)
    apply_to_right_edge = BitField(1, 0x04, as_bool=True, default=False)
    apply_to_bottom_edge = BitField(1, 0x08, as_bool=True, default=False)
    color_idx = BitField(2, 0x1F, default=0)

    apply_continuous_feedback_color = Field(default=False, serializable=False)
    apply_slow_blinking_feedback_color = Field(default=False, serializable=False)
    apply_fast_blinking_feedback_color = Field(default=False, serializable=False)
    apply_to_page = Field(default=None, serializable=False)
    apply_to_all_pages = Field(default=False, serializable=False)
    background_blinking = Field(default=False, serializable=False)
    custom_color_priority = Field(
        default=CustomColorPriority.LOW_PRIORITY, serializable=False
    )

    def data_to_binary(self):
        """:return: bytes"""
        byte_2 = (
            (0x80 if self.custom_color_palette else 0x00)
            | (0x01 if self.apply_background_color else 0x00)
            | (0x02 if self.apply_continuous_feedback_color else 0x00)
        )
        byte_3 = (
            (0x80 if self.apply_to_all_pages else 0x00)
            | (0x08 if self.apply_to_bottom_edge else 0x00)
            | (0x04 if self.apply_to_right_edge else 0x00)
            | (0x02 if self.apply_to_top_edge else 0x00)
            | (0x01 if self.apply_to_left_edge else 0x00)
        )
        byte_4 = (
            (0x80 if self.background_blinking else 0x00)
            | (self.custom_color_priority << 5)
            | (self.color_idx & 0x1F)
        )
        return bytes([COMMAND_CODE, byte_2, byte_3, byte_4])


class SetCustomColorMessage(DeclarativeMessage):
    """Set Custom Color (Palette) message (DLC=6 variant)."""

    _command_code = COMMAND_CODE
    _auto_register = False

    palette_idx = Field(default=0, serializable=False)
    white_mode = Field(default=False, serializable=False)
    saturation = Field(default=127, serializable=False)
    red = Field(default=0, serializable=False)
    green = Field(default=0, serializable=False)
    blue = Field(default=0, serializable=False)

    def data_to_binary(self):
        """:return: bytes"""
        byte_3 = (0x80 if self.white_mode else 0x00) | (self.saturation & 0x7F)
        return bytes(
            [
                COMMAND_CODE,
                self.palette_idx & 0x1F,
                byte_3,
                self.red,
                self.green,
                self.blue,
            ]
        )
