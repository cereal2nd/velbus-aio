"""Kwh Status message class (alias of counter status 0xBE).

:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.messages.counter_status import (
    COMMAND_CODE,
    CounterStatusBaseMessage,
    KwhStatusMessage,
)

__all__ = ["COMMAND_CODE", "CounterStatusBaseMessage", "KwhStatusMessage"]
