"""Fixtures for Signum Manager client tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest_asyncio

from fake_manager import FakeManager

_INSTALLATION = json.loads(
    (Path(__file__).with_name("installation.json")).read_text()
)


@pytest_asyncio.fixture
async def open_manager() -> FakeManager:
    """Started fake manager with authentication disabled."""
    manager = FakeManager(_INSTALLATION)
    await manager.start()
    yield manager
    await manager.stop()
