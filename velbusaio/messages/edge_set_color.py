"""Set Edge Color message class."""

from __future__ import annotations

from enum import IntEnum

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xD4


class CustomColorPriority(IntEnum):
    """Custom Color Priority enum."""

    LOW_PRIORITY = 1
    MID_PRIORITY = 2
    HIGH_PRIORITY = 3


@register(COMMAND_CODE, ["VMBEL1", "VMBEL2", "VMBEL4", "VMBELO", "VMBELO-20"])
class SetEdgeColorMessage(Message):
    """Set Edge Color message (DLC=4 variant)."""

    command_code = COMMAND_CODE

    def __init__(self, address=None):
        """Iniatialize Set Edge Color message object."""
        super().__init__()
        self.apply_background_color = False
        self.apply_continuous_feedback_color = False
        self.apply_slow_blinking_feedback_color = False
        self.apply_fast_blinking_feedback_color = False
        self.custom_color_palette = False

        self.apply_to_left_edge = False
        self.apply_to_top_edge = False
        self.apply_to_right_edge = False
        self.apply_to_bottom_edge = False

        self.apply_to_page: int | None = None
        self.apply_to_all_pages = False

        self.background_blinking = False
        self.custom_color_priority = CustomColorPriority.LOW_PRIORITY

        self.color_idx: int = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)
        self.apply_background_color = bool(data[0] & 0x01)
        self.custom_color_palette = bool(data[0] & 0x80)
        self.apply_to_left_edge = bool(data[1] & 0x01)
        self.apply_to_top_edge = bool(data[1] & 0x02)
        self.apply_to_right_edge = bool(data[1] & 0x04)
        self.apply_to_bottom_edge = bool(data[1] & 0x08)
        self.color_idx = data[2] & 0x1F

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


class SetCustomColorMessage(Message):
    """Set Custom Color (Palette) message (DLC=6 variant)."""

    def __init__(self, address=None):
        """Iniatialize Set Custom Color message object."""
        super().__init__()
        self.palette_idx = 0
        self.white_mode = False
        self.saturation = 127
        self.red = 0
        self.green = 0
        self.blue = 0
        self.set_defaults(address)

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
