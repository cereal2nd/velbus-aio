"""Switch Relay Off Message."""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ChannelsField, DeclarativeMessage

COMMAND_CODE = 0x02


@register(COMMAND_CODE)
class SwitchRelayOnMessage(DeclarativeMessage):
    """Switch Relay On Message."""

    _command_code = COMMAND_CODE
    _priority = "high"
    _data_length = 1

    relay_channels = ChannelsField(0)


@register(COMMAND_CODE, ["VMB4RYLD-20", "VMB4RYNO-20", "VMB1RYS-20"])
class SwitchRelayOnMessage20(SwitchRelayOnMessage):
    """Switch Relay On Message for -20 series."""

    def data_to_binary(self):
        """:return: bytes"""
        if self.relay_channels:
            return bytes([COMMAND_CODE, self.relay_channels[0]])
        return bytes([COMMAND_CODE, 0])
