"""Edge-lit panel Velbus channels."""

from __future__ import annotations

from velbusaio.channels.base import Channel
from velbusaio.messages.edge_set_color import (
    CustomColorPriority,
    SetCustomColorMessage,
    SetEdgeColorMessage,
)


class EdgeLit(Channel):
    """An EdgeLit channel."""

    def get_categories(self) -> list[str]:
        """Return the categories for this channel."""
        return ["light"]

    async def reset_color(
        self,
        left: bool = True,
        top: bool = True,
        right: bool = True,
        bottom: bool = True,
    ) -> None:
        """Send the edgelit color message."""
        msg = SetEdgeColorMessage(self._address)
        msg.apply_background_color = True
        msg.color_idx = 0
        msg.apply_to_left_edge = left
        msg.apply_to_top_edge = top
        msg.apply_to_right_edge = right
        msg.apply_to_bottom_edge = bottom
        msg.apply_to_all_pages = True
        await self._writer(msg)

    async def set_color(
        self,
        color_idx: int,
        left: bool = True,
        top: bool = True,
        right: bool = True,
        bottom: bool = True,
        blinking: bool = False,
        priority: CustomColorPriority = CustomColorPriority.LOW_PRIORITY,
    ) -> None:
        """Send the set color message."""

        msg = SetEdgeColorMessage(self._address)
        msg.apply_background_color = True
        msg.background_blinking = blinking
        msg.color_idx = color_idx
        msg.apply_to_left_edge = left
        msg.apply_to_top_edge = top
        msg.apply_to_right_edge = right
        msg.apply_to_bottom_edge = bottom
        msg.apply_to_all_pages = True
        msg.custom_color_priority = priority
        await self._writer(msg)

    async def set_rgbw(
        self,
        red: int,
        green: int,
        blue: int,
        white: int,
        left: bool = False,
        top: bool = False,
        right: bool = False,
        bottom: bool = False,
    ) -> None:
        """Set RGBW color for specific edges using a dedicated palette index per side."""
        # Mapping sides to palette indices
        if left:
            palette_idx = 1
        elif top:
            palette_idx = 2
        elif right:
            palette_idx = 3
        elif bottom:
            palette_idx = 4
        else:
            return  # No side specified

        # If all components are 0, we turn the edge OFF by using the default black palette (Index 0)
        if red == 0 and green == 0 and blue == 0 and white == 0:
            msg_apply = SetEdgeColorMessage(self._address)
            msg_apply.apply_background_color = True
            msg_apply.custom_color_palette = False  # USE DEFAULT PALETTE
            msg_apply.color_idx = 0  # BLACK
            msg_apply.apply_to_left_edge = left
            msg_apply.apply_to_top_edge = top
            msg_apply.apply_to_right_edge = right
            msg_apply.apply_to_bottom_edge = bottom
            msg_apply.apply_to_all_pages = True
            await self._writer(msg_apply)
            return

        # 1. Update the custom palette color
        msg_palette = SetCustomColorMessage(self._address)
        msg_palette.palette_idx = palette_idx
        msg_palette.red = red
        msg_palette.green = green
        msg_palette.blue = blue
        # If white is provided, we enable the official white_mode
        # This tells the module to use its internal white settings
        msg_palette.white_mode = white > 128
        msg_palette.saturation = 127  # Max saturation
        await self._writer(msg_palette)

        # 2. Apply this custom palette index to the requested edge
        msg_apply = SetEdgeColorMessage(self._address)
        msg_apply.apply_background_color = True
        msg_apply.custom_color_palette = True  # USE CUSTOM PALETTE
        msg_apply.color_idx = palette_idx
        msg_apply.apply_to_left_edge = left
        msg_apply.apply_to_top_edge = top
        msg_apply.apply_to_right_edge = right
        msg_apply.apply_to_bottom_edge = bottom
        msg_apply.apply_to_all_pages = True
        await self._writer(msg_apply)
