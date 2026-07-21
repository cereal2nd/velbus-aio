#!/usr/bin/env python3
"""Validate CommandToClass entries in module specs.

Checks that each module spec defines the basic messages required for its
channel types and that channel-name command variants are consistent.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from velbusaio.command_registry import MESSAGE_CATALOG, MODULE_DIRECTORY  # noqa: E402
import velbusaio.messages  # noqa: F401,E402 - populate MESSAGE_CATALOG

_MAX_UP_LEVELS = 6

GLOBAL_COMMANDS = frozenset(
    {"C9", "CA", "CB", "CC", "D9", "DA", "FA", "FC", "FD", "FE"}
)

MODULE_STATUS_CLASSES = frozenset(
    {
        "ModuleStatusMessage",
        "ModuleStatusMessage2",
        "ModuleStatusPirMessage",
        "ModuleStatusGP4PirMessage",
    }
)

RELAY_STATUS_CLASSES = frozenset(
    {"RelayStatusMessage", "RelayStatusMessage2", "RelayStatusMessage3"}
)

DIMMER_STATUS_COMMANDS = frozenset({"EE", "B8"})
TEMPERATURE_STATUS_COMMANDS = frozenset({"EA", "E6"})

THERMOSTAT_ONLY_TYPES = frozenset({"Temperature", "ThermostatChannel"})

CHANNEL_NAME_SETS = frozenset(
    {
        (
            "ChannelNameRequestMessage",
            "ChannelNamePart1Message",
            "ChannelNamePart2Message",
            "ChannelNamePart3Message",
        ),
        (
            "ChannelNameRequestMessage2",
            "ChannelNamePart1Message2",
            "ChannelNamePart2Message2",
            "ChannelNamePart3Message2",
        ),
        (
            "ChannelNameRequestMessage3",
            "ChannelNamePart1Message2",
            "ChannelNamePart2Message2",
            "ChannelNamePart3Message2",
        ),
        (
            "ChannelNameRequestMessage",
            "ChannelNamePart1Message2",
            "ChannelNamePart2Message2",
            "ChannelNamePart3Message2",
        ),
        (
            "ChannelNameRequestMessage",
            "ChannelNamePart1Message3",
            "ChannelNamePart2Message3",
            "ChannelNamePart3Message3",
        ),
        (
            "ChannelNameRequestMessage2",
            "ChannelNamePart1Message3",
            "ChannelNamePart2Message3",
            "ChannelNamePart3Message3",
        ),
    }
)

GP_CHANNEL_NAME_SET = (
    "ChannelNameRequestMessage",
    "ChannelNamePart1Message2",
    "ChannelNamePart2Message2",
    "ChannelNamePart3Message2",
)


def locate_module_spec_dir(start: Path | None = None) -> Path | None:
    """Locate velbusaio/module_spec by walking up from start."""
    if start is None:
        start = Path(__file__).resolve().parent

    path = start
    for _ in range(_MAX_UP_LEVELS):
        candidate = path / "velbusaio" / "module_spec"
        if candidate.is_dir():
            return candidate
        path = path.parent
    return None


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def merged_command_to_class(global_ctc: dict[str, str], spec: dict) -> dict[str, str]:
    return {**global_ctc, **spec.get("CommandToClass", {})}


def channel_types(spec: dict) -> set[str]:
    return {chan.get("Type", "") for chan in spec.get("Channels", {}).values()}


def has_editable_channels(spec: dict) -> bool:
    return any(chan.get("Editable") == "yes" for chan in spec.get("Channels", {}).values())


def max_editable_channel(spec: dict) -> int:
    numbers = [
        int(chan_key)
        for chan_key, chan in spec.get("Channels", {}).items()
        if chan.get("Editable") == "yes"
    ]
    return max(numbers, default=0)


def needs_module_status(spec: dict, types: set[str]) -> bool:
    if "ButtonCounter" in types:
        return True
    if "AllChannelStatus" not in spec:
        return False
    if not types:
        return False
    return not types.issubset(THERMOSTAT_ONLY_TYPES)


def validate_global_commands(global_path: Path, global_ctc: dict[str, str]) -> list[str]:
    errors: list[str] = []
    missing = sorted(GLOBAL_COMMANDS - set(global_ctc))
    if missing:
        errors.append(
            f"{global_path}: global.json missing universal commands: {', '.join(missing)}"
        )
    for command_hex, class_name in global_ctc.items():
        if class_name not in MESSAGE_CATALOG:
            errors.append(
                f"{global_path}: CommandToClass {command_hex} references unknown class "
                f"{class_name}"
            )
    return errors


def validate_module_spec(
    path: Path, spec: dict, merged: dict[str, str]
) -> list[str]:
    errors: list[str] = []
    module_name = spec.get("Type", path.stem)
    types = channel_types(spec)
    editable = has_editable_channels(spec)

    for command_hex, class_name in spec.get("CommandToClass", {}).items():
        try:
            int(command_hex, 16)
        except ValueError:
            errors.append(f"{path}: invalid CommandToClass key {command_hex}")
        if class_name not in MESSAGE_CATALOG:
            errors.append(
                f"{path}: CommandToClass {command_hex} references unknown class "
                f"{class_name}"
            )

    if "Button" in types and "00" not in merged:
        errors.append(f"{path} ({module_name}): has Button channels but missing 00")

    if "Relay" in types and "AllChannelStatus" not in spec and "FB" not in merged:
        errors.append(f"{path} ({module_name}): has Relay channels but missing FB")
    if "Relay" in types and "FB" in merged and merged["FB"] not in RELAY_STATUS_CLASSES:
        errors.append(
            f"{path} ({module_name}): invalid relay status class {merged['FB']}"
        )

    if "Dimmer" in types and not DIMMER_STATUS_COMMANDS.intersection(merged):
        errors.append(f"{path} ({module_name}): has Dimmer channels but missing EE/B8")

    if "Blind" in types and "EC" not in merged:
        errors.append(f"{path} ({module_name}): has Blind channels but missing EC")

    if "Temperature" in types and not TEMPERATURE_STATUS_COMMANDS.intersection(merged):
        errors.append(
            f"{path} ({module_name}): has Temperature channels but missing EA/E6"
        )

    if needs_module_status(spec, types):
        if "ED" not in merged:
            errors.append(f"{path} ({module_name}): missing module status response ED")
        elif merged["ED"] not in MODULE_STATUS_CLASSES:
            errors.append(
                f"{path} ({module_name}): invalid module status class {merged['ED']}"
            )

    if editable:
        name_cmds = tuple(merged.get(cmd) for cmd in ("EF", "F0", "F1", "F2"))
        if None in name_cmds:
            errors.append(
                f"{path} ({module_name}): editable channels but missing channel name "
                "commands EF/F0/F1/F2"
            )
        elif name_cmds not in CHANNEL_NAME_SETS:
            errors.append(
                f"{path} ({module_name}): inconsistent channel name commands {name_cmds}"
            )
        elif max_editable_channel(spec) > 8 and name_cmds != GP_CHANNEL_NAME_SET:
            errors.append(
                f"{path} ({module_name}): editable channel > 8 requires "
                f"{GP_CHANNEL_NAME_SET}, got {name_cmds}"
            )

    return errors


def validate_all(module_spec_dir: Path) -> list[str]:
    errors: list[str] = []
    global_path = module_spec_dir / "global.json"
    global_spec = load_json(global_path)
    global_ctc = global_spec.get("CommandToClass", {})
    errors.extend(validate_global_commands(global_path, global_ctc))

    for module_type, module_name in sorted(MODULE_DIRECTORY.items()):
        spec_path = module_spec_dir / f"{module_type:02X}.json"
        if not spec_path.exists():
            errors.append(
                f"Module type 0x{module_type:02X} ({module_name}) has no spec file"
            )
            continue
        spec = load_json(spec_path)
        if spec.get("Type") != module_name:
            errors.append(
                f"{spec_path}: Type={spec.get('Type')!r} does not match "
                f"MODULE_DIRECTORY entry {module_name!r}"
            )
        merged = merged_command_to_class(global_ctc, spec)
        errors.extend(validate_module_spec(spec_path, spec, merged))

    return errors


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    start_path = Path(argv[0]).resolve() if argv else None
    module_spec_dir = locate_module_spec_dir(start_path)
    if module_spec_dir is None:
        print(
            "Could not find velbusaio/module_spec directory.",
            file=sys.stderr,
        )
        return 1

    errors = validate_all(module_spec_dir)
    if errors:
        print("Command spec validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Command spec validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
