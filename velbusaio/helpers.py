"""Helper functions."""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any

from velbusaio.const import CACHEDIR


def keys_exists(element: dict[str, Any], *keys) -> dict:
    """Check if *keys (nested) exists in `element` (dict)."""
    if not isinstance(element, dict):
        raise TypeError("keys_exists() expects dict as first argument.")
    if len(keys) == 0:
        raise AttributeError("keys_exists() expects at least two arguments, one given.")

    _element = element
    for key in keys:
        _element = _element.get(key)
        if _element is None:
            return False
    return _element


def h2(inp: int) -> str:
    """Format as hex uppercase."""
    return format(inp, "02x").upper()


def handle_match(match_dict: dict[str, dict[str, dict[str, str]]], data: int) -> dict:
    """Handle memory match from the module data."""
    match_result = {}
    binary_data = f"{int(data):08b}"
    for num, match_data in match_dict.items():
        tmp = {}
        for match, res in match_data.items():
            if re.fullmatch(match[1:], binary_data):
                res2 = res.copy()
                res2["Data"] = int(data)
                tmp.update(res2)
        match_result[num] = tmp
    result = {}
    for res in match_result.values():
        if "Channel" in res:
            result[int(res["Channel"])] = {}
            if "SubName" in res and "Value" in res and res["Value"] != "PulsePerUnits":
                result[int(res["Channel"])] = {res["SubName"]: res["Value"]}
            else:
                # Very specifick for vmb7in
                # a = bit 0 to 5 = 0 to 63
                # b = a * 100
                multi = (data & 0x3F) * 100
                # c = bit 6 + 7
                #   00 = x1
                #   01 = x2,5
                #   10 = x0.05
                #   11 = x0.01
                # d = b * c
                if data >> 5 == 3:
                    val = multi * 0.01
                elif data >> 5 == 2:
                    val = multi * 0.05
                elif data >> 5 == 1:
                    val = multi * 2.5
                else:
                    val = multi
                result[int(res["Channel"])] = {res["Value"]: val}
    return result


def get_cache_dir() -> str:
    """Put together the default configuration directory based on the OS."""
    data_dir = os.getenv("APPDATA") if os.name == "nt" else str(Path("~").expanduser())
    return str(Path(data_dir) / CACHEDIR)
