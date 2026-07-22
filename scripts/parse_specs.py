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

# Add parent directory to path to import velbusaio and sibling scripts
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from velbusaio.command_registry import MESSAGE_CATALOG, MODULE_DIRECTORY  # noqa: E402
import velbusaio.messages  # noqa: F401,E402 - populate MESSAGE_CATALOG

from validate_command_specs import validate_all  # noqa: E402

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


def _unsorted_keys(data: Any, path: str = "") -> list[str]:
    """Recursively find dict keys that are not sorted alphabetically."""
    errors: list[str] = []
    if isinstance(data, dict):
        keys = list(data.keys())
        if keys != sorted(keys):
            errors.append(f"  at '{path}': {keys} (expected {sorted(keys)})")
        for key, value in data.items():
            errors.extend(_unsorted_keys(value, f"{path}.{key}" if path else key))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            errors.extend(_unsorted_keys(item, f"{path}[{i}]"))
    return errors


def check_json_sorted(path: Path) -> list[str]:
    """Check that all JSON keys are sorted alphabetically at every level."""
    try:
        spec = load_json(path)
    except Exception as exc:
        return [f"{path}: failed to load JSON: {exc}"]
    issues = _unsorted_keys(spec)
    if issues:
        return [f"{path}: keys not sorted:"] + issues
    return []


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
            if chan_data.get("Editable", "") == "yes" and (
                mem_channels is None or possible_key not in mem_channels
            ):
                errors.append(
                    f"{path}: channel {chan_num} of type {ctype} is editable but no memory location found in Memory->Channels for key {possible_key}"
                )

    return errors


def validate_command_to_class(path: Path, spec: dict) -> list[str]:
    """Validate CommandToClass entries reference known message classes."""
    errors: list[str] = []
    mapping = spec.get("CommandToClass")
    if not mapping:
        return errors
    for command_hex, class_name in mapping.items():
        try:
            int(command_hex, 16)
        except ValueError:
            errors.append(f"{path}: invalid CommandToClass key {command_hex}")
        if class_name not in MESSAGE_CATALOG:
            errors.append(
                f"{path}: CommandToClass {command_hex} references unknown class {class_name}"
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


# Spec files that are not module-type specs and therefore have no
# MODULE_DIRECTORY entry.
_NON_MODULE_SPECS = frozenset({"global", "broadcast", "ignore"})


def check_orphan_specs(module_spec_dir: Path) -> list[str]:
    """Check that every module-type spec file has a MODULE_DIRECTORY entry.

    This is the reverse of check_module_directory_coverage: it reports spec files
    that exist on disk but are not referenced by MODULE_DIRECTORY (orphan specs),
    so the library would never instantiate them.
    """
    errors: list[str] = []
    known_types = {h2(module_type).upper() for module_type in MODULE_DIRECTORY}

    for spec_path in sorted(module_spec_dir.glob("*.json")):
        stem = spec_path.stem
        if stem.lower() in _NON_MODULE_SPECS:
            continue
        try:
            int(stem, 16)
        except ValueError:
            # Not a hex-named module spec (e.g. a helper file); skip it.
            continue
        if stem.upper() not in known_types:
            errors.append(
                f"Spec file {spec_path.name} has no MODULE_DIRECTORY entry "
                f"(orphan spec: 0x{stem.upper()} is not registered)"
            )

    return errors


def check_empty_command_to_class(module_spec_dir: Path) -> list[str]:
    """Check that every module-type spec defines a non-empty CommandToClass.

    A module spec with a missing or empty CommandToClass cannot decode any bus
    message, so it is almost certainly incomplete.
    """
    warnings: list[str] = []

    for spec_path in sorted(module_spec_dir.glob("*.json")):
        stem = spec_path.stem
        if stem.lower() in _NON_MODULE_SPECS:
            continue
        try:
            int(stem, 16)
        except ValueError:
            continue
        try:
            spec = load_json(spec_path)
        except Exception as exc:
            warnings.append(f"{spec_path.name}: failed to load JSON: {exc}")
            continue
        if not spec.get("CommandToClass"):
            warnings.append(
                f"Spec file {spec_path.name} has an empty or missing CommandToClass"
            )

    return warnings


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
        try:
            spec = load_json(p)
        except Exception as exc:
            all_errors.append(f"{p}: failed to load JSON: {exc}")
            continue
        all_errors.extend(validate_spec(p))
        all_errors.extend(validate_command_to_class(p, spec))
        all_errors.extend(check_json_sorted(p))

    # Validate CommandToClass coverage for basic messages
    print("\nValidating CommandToClass coverage...")
    command_errors = validate_all(module_spec_dir)
    all_errors.extend(command_errors)
    if command_errors:
        print(f"Found {len(command_errors)} CommandToClass problems.")
    else:
        print("All CommandToClass entries are complete and consistent.")

    # Non-fatal warnings: orphan specs and empty CommandToClass.
    all_warnings: list[str] = []
    all_warnings.extend(check_orphan_specs(module_spec_dir))
    all_warnings.extend(check_empty_command_to_class(module_spec_dir))
    if all_warnings:
        print(f"\nWarnings ({len(all_warnings)}):")
        for w in all_warnings:
            print(f" - {w}")

    if all_errors:
        print("\nModule spec validation failed. Problems found:")
        for e in all_errors:
            print(f" - {e}")
        return 1

    print("\nModule spec validation passed:")
    print(" - All modules in MODULE_DIRECTORY have spec files")
    print(" - All editable channels have memory locations")
    print(" - All CommandToClass entries reference known message classes")
    print(" - All JSON files have alphabetically sorted keys")
    print(" - All CommandToClass entries are complete and consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
