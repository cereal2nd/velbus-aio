"""Tests for Module._get_cache handling of empty and malformed cache files.

Regression test for https://github.com/cereal2nd/velbus-aio/issues/140
(crash on empty module cache file).
"""

import asyncio
import json
import logging
import pathlib

import pytest

from velbusaio.module import Module

VMBGP4 = 0x20


def _make_module(cache_dir: pathlib.Path) -> Module:
    module = Module(0x01, VMBGP4, cache_dir=str(cache_dir))
    module._log = logging.getLogger("velbus-module")
    return module


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [
        "",  # empty file
        "   \n  ",  # whitespace only
        "garbage",  # invalid json
        "null",  # valid json, but not a mapping
        "[]",  # valid json list
        "42",  # valid json number
    ],
)
async def test_get_cache_invalid_returns_empty_and_removes_file(tmp_path, content):
    module = _make_module(tmp_path)
    cfile = tmp_path / "1.json"
    cfile.write_text(content)

    cache = await module._get_cache()

    assert cache == {}
    # corrupt/unusable cache files are removed so they are treated as absent
    assert not cfile.exists()


@pytest.mark.asyncio
async def test_get_cache_missing_file_returns_empty(tmp_path):
    module = _make_module(tmp_path)

    cache = await module._get_cache()

    assert cache == {}


@pytest.mark.asyncio
async def test_get_cache_valid_dict_is_preserved(tmp_path):
    module = _make_module(tmp_path)
    cfile = tmp_path / "1.json"
    cfile.write_text('{"name": "kitchen", "channels": {}}')

    cache = await module._get_cache()

    assert cache == {"name": "kitchen", "channels": {}}
    assert cfile.exists()


@pytest.mark.asyncio
async def test_to_cache_name_falls_back_to_type_name(tmp_path):
    """A module without a programmed name caches its type name, not ''."""
    module = _make_module(tmp_path)
    module._data = {"Type": "VMBDALI-20"}
    # _name is still the initial value (no name was ever assembled)
    assert not isinstance(module._name, str)

    cache = module.to_cache()

    assert cache["name"] == "VMBDALI-20"


@pytest.mark.asyncio
async def test_write_cache_persists_unloaded_module(tmp_path):
    """A found-but-not-loaded module still gets a valid cache file.

    Regression test: a module discovered on the bus that never reaches the
    fully-loaded state (e.g. an unresponsive DALI module) used to leave no
    ``{address}.json`` behind because ``_cache()`` is only triggered on the
    loaded transition / name completion.
    """
    module = _make_module(tmp_path)
    module._data = {"Type": "VMBDALI-20"}
    cfile = tmp_path / "1.json"
    assert not cfile.exists()

    await module.write_cache()

    assert cfile.exists()
    data = json.loads(cfile.read_text())
    assert data["name"] == "VMBDALI-20"
    assert "channels" in data


@pytest.mark.asyncio
async def test_concurrent_cache_writes_leave_valid_json(tmp_path):
    """Concurrent _cache() calls must never leave a corrupt cache file.

    Regression test: two coroutines opening the same file in truncate
    mode could interleave writes, leaving trailing garbage after a valid
    JSON object ("Extra data" corruption).
    """
    module = _make_module(tmp_path)
    cfile = tmp_path / "1.json"

    await asyncio.gather(*(module._cache() for _ in range(50)))

    # File is always valid JSON with no trailing junk
    content = cfile.read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict)
    assert parsed == module.to_cache()
    # No leftover temp files
    assert list(tmp_path.glob("*.tmp")) == []
