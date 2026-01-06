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


@register(COMMAND_CODE, ["VMBEL1", "VMBEL2", "VMBEL4", "VMBELO"])
class SetEdgeColorMessage(Message):
    """Set Edge Color message."""

    apply_background_color = False
    apply_continuous_feedback_color = False
    apply_slow_blinking_feedback_color = False
    apply_fast_blinking_feedback_color = False
    custom_color_palette = False

    apply_to_left_edge = False
    apply_to_top_edge = False
    apply_to_right_edge = False
    apply_to_bottom_edge = False

    apply_to_page: int | None = None
    apply_to_all_pages = False

    background_blinking = False
    custom_color_priority: CustomColorPriority | None = None

    color_idx: int = 0

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)

        self.apply_background_color = bool(data[0] & 0x01)
        self.apply_continuous_feedback_color = bool(data[0] & 0x02)
        self.apply_slow_blinking_feedback_color = bool(data[0] & 0x04)
        self.apply_fast_blinking_feedback_color = bool(data[0] & 0x08)
        self.custom_color_palette = bool(data[0] & 0x80)

        self.apply_to_left_edge = bool(data[1] & 0x01)
        self.apply_to_top_edge = bool(data[1] & 0x02)
        self.apply_to_right_edge = bool(data[1] & 0x04)
        self.apply_to_bottom_edge = bool(data[1] & 0x08)

        page = (data[1] & 0b0111_0000) >> 4
        if page > 0:
            self.apply_to_page = page
        self.apply_to_all_pages = bool(data[1] & 0x80)

        self.background_blinking = bool(data[2] & 0x80)

        custom_color_priority_value = data[2] & 0b0110_0000 >> 5
        if custom_color_priority_value:
            self.custom_color_priority = CustomColorPriority(
                custom_color_priority_value
            )

        self.color_idx = data[2] & 0b0001_1111

    def data_to_binary(self):
        """:return: bytes"""

        byte_2 = (
            self.apply_background_color * 0x01
            + self.apply_continuous_feedback_color * 0x02
            + self.apply_slow_blinking_feedback_color * 0x04
            + self.apply_fast_blinking_feedback_color * 0x08
            + self.custom_color_palette * 0x80
        )

        byte_3 = (
            self.apply_to_left_edge * 0x01
            + self.apply_to_top_edge * 0x02
            + self.apply_to_right_edge * 0x04
            + self.apply_to_bottom_edge * 0x08
            + (((self.apply_to_page or 0) & 0xFFF) << 4)
            + self.apply_to_all_pages * 0x80
        )

        byte_4 = (
            (self.color_idx & 0xFFFF)
            + (
                (int(self.custom_color_priority) if self.custom_color_priority else 0)
                << 5
            )
            + self.background_blinking * 0x80
        )

        return bytes(
            [
                COMMAND_CODE,
                byte_2,
                byte_3,
                byte_4,
            ]
        )
