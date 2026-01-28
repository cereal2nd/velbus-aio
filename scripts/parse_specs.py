#!/usr/bin/env python3
"""Validate module spec JSON files.

This script checks all JSON files under velbusaio/module_spec/*.json and fails
if any module spec declares a channel with "Editable": "yes" but the module
spec does not contain the corresponding memory location under
"Memory" -> "Channels" for that channel.

Additionally, it validates that every module type in the MODULE_DIRECTORY from
command_registry.py has a corresponding module spec file.

This version fixes an AttributeError caused by MODULE_SPEC_DIR being a string
instead of a pathlib.Path and makes locating the module_spec directory more
robust (walks up from the script location to find the repo root).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

# Add parent directory to path to import velbusaio
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from velbusaio.command_registry import MODULE_DIRECTORY

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


def check_module_directory_coverage(module_spec_dir: Path) -> list[str]:
    """Check that every module in MODULE_DIRECTORY has a corresponding spec file."""
    errors: list[str] = []

    # Get all existing spec files (without .json extension)
    existing_specs = {p.stem.upper(): p for p in module_spec_dir.glob("*.json")}

    # Check each module in the registry
    for module_type, module_name in MODULE_DIRECTORY.items():
        expected_filename = h2(module_type).upper()

        if expected_filename not in existing_specs:
            errors.append(
                f"Module type 0x{expected_filename} ({module_name}) from MODULE_DIRECTORY "
                f"has no corresponding spec file {expected_filename}.json"
            )
        else:
            # Spec file exists, now check if the Type field matches the module name
            spec_path = existing_specs[expected_filename]
            try:
                spec = load_json(spec_path)
                spec_type = spec.get("Type")

                if spec_type is None:
                    errors.append(
                        f"Spec file {spec_path.name} is missing 'Type' field "
                        f"(expected: {module_name})"
                    )
                elif spec_type != module_name:
                    errors.append(
                        f"Spec file {spec_path.name} has Type='{spec_type}' "
                        f"but MODULE_DIRECTORY[0x{expected_filename}] expects '{module_name}'"
                    )
            except Exception as exc:
                errors.append(
                    f"Failed to validate Type field in {spec_path.name}: {exc}"
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

    # Check that all modules in MODULE_DIRECTORY have spec files
    print("Checking MODULE_DIRECTORY coverage...")
    coverage_errors = check_module_directory_coverage(module_spec_dir)
    all_errors.extend(coverage_errors)

    if coverage_errors:
        print(f"Found {len(coverage_errors)} modules without spec files.")
    else:
        print("All modules in MODULE_DIRECTORY have spec files.")

    # Validate individual spec files
    print(f"\nValidating {len(spec_files)} module spec files...")
    for p in spec_files:
        errs = validate_spec(p)
        all_errors.extend(errs)

    if all_errors:
        print("\nModule spec validation failed. Problems found:")
        for e in all_errors:
            print(f" - {e}")
        return 1

    print("\nModule spec validation passed:")
    print(" - All modules in MODULE_DIRECTORY have spec files")
    print(" - All editable channels have memory locations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
