"""Tests for Module._get_cache handling of empty and malformed cache files.

Regression test for https://github.com/cereal2nd/velbus-aio/issues/140
(crash on empty module cache file).
"""

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
