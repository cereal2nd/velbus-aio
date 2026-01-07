#!/usr/bin/env python3
"""Validate module spec JSON files.

This script checks all JSON files under velbusaio/module_spec/*.json and fails
if any module spec declares a channel with "Editable": "yes" but the module
spec does not contain the corresponding memory location under
"Memory" -> "Channels" for that channel.

This version fixes an AttributeError caused by MODULE_SPEC_DIR being a string
instead of a pathlib.Path and makes locating the module_spec directory more
robust (walks up from the script location to find the repo root).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

# How many directory levels to walk up from this script to try to find the repo root
_MAX_UP_LEVELS = 6


def h2(n: int) -> str:
    """Format an integer as the two-digit uppercase hex used in specs (e.g. 1 -> '01')."""
    return f"{int(n):02X}"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def locate_module_spec_dir(start: Path | None = None) -> Path | None:
    """Locate velbusaio/module_spec by walking up from start (defaults to this script's dir).
    Returns a pathlib.Path if found, otherwise None.
    """
    if start is None:
        start = Path(__file__).resolve().parent

    p = start
    for _ in range(_MAX_UP_LEVELS):
        candidate = p / "velbusaio" / "module_spec"
        if candidate.is_dir():
            return candidate
        p = p.parent
    return None


def validate_spec(path: Path) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        spec = load_json(path)
    except Exception as exc:
        errors.append(f"{path}: failed to load JSON: {exc}")
        return errors

    channels = spec.get("Channels", {})
    memory = spec.get("Memory")

    for chan_key, chan_data in channels.items():
        try:
            chan_num = int(chan_key)
        except Exception:
            errors.append(f"{path}: channel key '{chan_key}' is not an integer")
            continue

        editable = chan_data.get("Editable", "") == "yes"

        if memory is None:
            errors.append(
                f"{path}: channel {chan_num} (editable) but module spec is missing top-level 'Memory'"
            )
            continue

        mem_channels = memory.get("Channels")
        if mem_channels is None:
            warnings.append(
                f"{path}: channel {chan_num} (editable) but 'Memory' does not contain 'Channels'"
            )
            continue

        possible_key = str(chan_num).zfill(2)

        if possible_key not in mem_channels and editable:
            errors.append(
                f"{path}: channel {chan_num} (editable) but no memory location found in Memory->Channels for key {possible_key}"
            )

        ctype = chan_data.get("Type", "")
        if ctype in [
            "Blind",
            "Button",
            "ButtonCounter",
            "Dimmer",
            "Temperature",
            "Relay",
        ]:
            if chan_data.get("Editable", "") == "":
                errors.append(
                    f"{path}: channel {chan_num} of type {ctype} but editable field is missing"
                )
            if chan_data.get("Editable", "") == "yes":
                if mem_channels is None or possible_key not in mem_channels:
                    errors.append(
                        f"{path}: channel {chan_num} of type {ctype} is editable but no memory location found in Memory->Channels for key {possible_key}"
                    )

    return errors


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    # optional first arg: path to repo root (or path that contains velbusaio/module_spec)
    start_path = None
    if len(argv) >= 1 and argv[0].strip():
        start_path = Path(argv[0]).resolve()

    module_spec_dir = locate_module_spec_dir(start_path)
    if module_spec_dir is None:
        print(
            "Could not find velbusaio/module_spec directory. "
            "Run the script from the repo or provide the repo path as the first argument.",
            file=sys.stderr,
        )
        return 1

    spec_files = sorted(module_spec_dir.glob("*.json"))
    if not spec_files:
        print(
            f"No module spec JSON files found under {module_spec_dir}", file=sys.stderr
        )
        return 1

    all_errors: list[str] = []
    for p in spec_files:
        errs = validate_spec(p)
        all_errors.extend(errs)

    if all_errors:
        print("Module spec validation failed. Problems found:")
        for e in all_errors:
            print(f" - {e}")
        return 1

    print("Module spec validation passed: all editable channels have memory locations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
