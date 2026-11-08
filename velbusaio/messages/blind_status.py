"""Blind Status message.

:author: Tom Dupré <gitd8400@gmail.com>
"""

from __future__ import annotations

from typing import Any

from velbusaio.command_registry import register
from velbusaio.json_labels import BLIND_STATUS_JSON_MAP
from velbusaio.message_fields import (
    BlindChannelField,
    BlindStatusField,
    ByteField,
    ChannelField,
    ComputedField,
    DeclarativeMessage,
)

COMMAND_CODE = 0xEC
DSTATUS = BLIND_STATUS_JSON_MAP


class BlindMovementMixin:
    """Movement helpers for blind status messages with integer ``status``."""

    status: int

    def is_moving_up(self) -> bool:
        """Is moving up."""
        return self.status == 0x01

    def is_moving_down(self) -> bool:
        """Is moving down."""
        return self.status == 0x02

    def is_stopped(self) -> bool:
        """Is stopped."""
        return self.status == 0x00


@register(COMMAND_CODE)
class BlindStatusNgMessage(BlindMovementMixin, DeclarativeMessage):
    """Blind Status NG message."""

    _command_code = COMMAND_CODE
    _data_length = 7
    _generates_data_to_binary = False
    _generates_to_json = True

    channel = ChannelField(0)
    timeout = ByteField(1)
    status = ByteField(2, json_map=DSTATUS)
    position = ByteField(4, default=None)


@register(COMMAND_CODE)
class BlindStatusNg20Message(BlindStatusNgMessage):
    """Blind Status NG20 message."""

    channel = ComputedField(
        parser=lambda data: (1, 2),
        default=(1, 2),
        serializable=False,
    )
    timeout = ComputedField(parser=lambda data: 0, default=0, serializable=False)
    status = ComputedField(
        parser=lambda data: (data[0] & 0x03, (data[0] >> 4) & 0x03),
        default=(0, 0),
        serializable=False,
    )
    position = ComputedField(
        parser=lambda data: (data[1], data[2]),
        default=(0, 0),
        serializable=False,
    )

    def to_json_basic(self) -> dict[str, Any]:
        """JSON dict with per-channel status labels."""
        payload = super().to_json_basic()
        payload["status"] = [DSTATUS[channel_status] for channel_status in self.status]
        return payload


@register(COMMAND_CODE)
class BlindStatusMessage(BlindMovementMixin, DeclarativeMessage):
    """Blind Status message."""

    _command_code = COMMAND_CODE
    _data_length = 7
    _generates_data_to_binary = False
    _generates_to_json = True

    channel = BlindChannelField(0)
    timeout = ByteField(1)
    status = BlindStatusField(2, json_map=DSTATUS)
