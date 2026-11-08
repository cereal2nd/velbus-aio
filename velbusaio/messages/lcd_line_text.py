"""LCD line text and backlight status (VMB4PD and similar)."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import BitField, DeclarativeMessage, StringField

COMMAND_LCD_PART1 = 0xCD
COMMAND_LCD_PART2 = 0xCE
COMMAND_LCD_PART3 = 0xCF
COMMAND_BACKLIGHT_STATUS = 0xD6


@register(COMMAND_LCD_PART1)
class LcdLineTextPart1Message(DeclarativeMessage):
    """First part of an LCD line text update (up to 6 characters)."""

    _command_code = COMMAND_LCD_PART1
    _data_length = 7
    _priority = "low"
    _generates_data_to_binary = False

    line = BitField(0, 0x0F, default=1)
    text = StringField(1, length=6)


@register(COMMAND_LCD_PART2)
class LcdLineTextPart2Message(DeclarativeMessage):
    """Second part of an LCD line text update (characters 7–12)."""

    _command_code = COMMAND_LCD_PART2
    _data_length = 7
    _priority = "low"
    _generates_data_to_binary = False

    line = BitField(0, 0x0F, default=1)
    text = StringField(1, length=6)


@register(COMMAND_LCD_PART3)
class LcdLineTextPart3Message(DeclarativeMessage):
    """Third part of an LCD line text update (characters 13–15)."""

    _command_code = COMMAND_LCD_PART3
    _data_length = 5
    _priority = "low"
    _generates_data_to_binary = False

    line = BitField(0, 0x0F, default=1)
    text = StringField(1, length=3)


@register(COMMAND_BACKLIGHT_STATUS)
class BacklightStatusMessage(DeclarativeMessage):
    """LCD and button backlight / contrast status."""

    _command_code = COMMAND_BACKLIGHT_STATUS
    _data_length = 1
    _priority = "low"
    _generates_data_to_binary = False

    status = BitField(0, 0xFF, default=0)
