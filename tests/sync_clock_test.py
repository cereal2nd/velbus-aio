"""Tests for Velbus.sync_clock."""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

from velbusaio.controller import Velbus
from velbusaio.messages.set_date import SetDate
from velbusaio.messages.set_daylight_saving import SetDaylightSaving
from velbusaio.messages.set_realtime_clock import SetRealtimeClock


@pytest.mark.asyncio
async def test_sync_clock_uses_passed_aware_datetime() -> None:
    """sync_clock encodes the provided timezone-aware datetime."""
    velbus = Velbus("")
    velbus.send = AsyncMock()

    # Friday 21 Feb 2025 13:30 in Brussels (CET, standard time, not DST)
    dt = datetime.datetime(2025, 2, 21, 13, 30, tzinfo=ZoneInfo("Europe/Brussels"))

    await velbus.sync_clock(dt)

    assert velbus.send.await_count == 3
    calls = [call.args[0] for call in velbus.send.await_args_list]

    assert isinstance(calls[0], SetRealtimeClock)
    assert calls[0]._wday == 4
    assert calls[0]._hour == 13
    assert calls[0]._min == 30

    assert isinstance(calls[1], SetDate)
    assert calls[1]._day == 21
    assert calls[1]._mon == 2
    assert calls[1]._year == 2025

    assert isinstance(calls[2], SetDaylightSaving)
    # ds=1 means standard time (inverted from is_dst in controller)
    assert calls[2]._ds == 1
