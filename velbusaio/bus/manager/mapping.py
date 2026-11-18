"""Map Signum Manager property names to velbusaio channel updates."""

from __future__ import annotations

from typing import Any

from velbusaio.bus.manager import channel_remap
from velbusaio.channels import ButtonCounter, Channel, Dimmer
from velbusaio.command_registry import MODULE_DIRECTORY
from velbusaio.module import Module

CHANNEL_REMAPS = channel_remap.CHANNEL_REMAPS
remap_channel_number = channel_remap.remap_channel_number

_TYPE_NAME_OVERRIDES: dict[str, str] = {
    "VMBDMI_R": "VMBDMI-R",
}

_NAME_TO_CODE: dict[str, int] = {name: code for code, name in MODULE_DIRECTORY.items()}

_LED_INBOUND = {
    "On": "on",
    "Off": "off",
    "Slow": "slow",
    "Fast": "fast",
    "VeryFast": "fast",
}

_MODE_MAP = {
    "Safe": "safe",
    "Comfort": "comfort",
    "Day": "day",
    "Night": "night",
    "CoolSafe": "safe",
    "CoolComfort": "comfort",
    "CoolDay": "day",
    "CoolNight": "night",
}


def manager_module_type_to_code(name: str) -> int:
    """Resolve a Signum moduleType string to a velbus type code."""
    normalized = _TYPE_NAME_OVERRIDES.get(name, name.replace("_", "-"))
    code = _NAME_TO_CODE.get(normalized)
    if code is None:
        raise ValueError(f"Unknown Signum module type {name!r}")
    return code


def parse_build_number(build: int | str) -> tuple[int, int]:
    """Split Signum buildNumber into firmware year and week."""
    text = f"{int(build):04d}" if isinstance(build, int) else build
    if len(text) < 4:
        text = text.zfill(4)
    return int(text[0:2]), int(text[2:4])


def map_properties_to_update(
    channel: Channel,
    properties: dict[str, Any],
) -> dict[str, Any]:
    """Translate Signum channel properties to velbusaio update keys."""
    updates: dict[str, Any] = {}
    if "On" in properties:
        updates["on"] = bool(properties["On"])
    if "Brightness" in properties:
        if isinstance(channel, Dimmer):
            percent = int(properties["Brightness"])
            updates["state"] = int(percent * channel.slider_scale / 100)
        else:
            updates["state"] = properties["Brightness"]
    if "Position" in properties:
        updates["position"] = int(properties["Position"])
    for key, state in (("Up", 0x01), ("Down", 0x02), ("Halt", 0x00)):
        if properties.get(key):
            updates["state"] = state
    if properties.get("Released"):
        updates["closed"] = False
        updates["on"] = False
        updates["long"] = False
    if properties.get("LongPressed"):
        updates["closed"] = True
        updates["long"] = True
    if properties.get("Pressed") and not properties.get("LongPressed"):
        updates["closed"] = True
        updates["on"] = True
    if "Led" in properties:
        led = properties["Led"]
        if isinstance(led, str):
            updates["led_state"] = _LED_INBOUND.get(led, led.lower())
        elif isinstance(led, bool):
            updates["led_state"] = "on" if led else "off"
    if "Temperature" in properties:
        updates["cur"] = float(properties["Temperature"])
    if "TargetTemperature" in properties:
        updates["target"] = float(properties["TargetTemperature"])
    if "TemperatureMode" in properties:
        mode = properties["TemperatureMode"]
        if isinstance(mode, str):
            updates["cmode"] = _MODE_MAP.get(mode, mode.lower())
        elif isinstance(mode, (int, float)):
            updates["cmode"] = str(mode)
    if "Cooling" in properties:
        updates["cool_mode"] = bool(properties["Cooling"])
    if properties.get("HasThermostat"):
        updates["thermostat"] = True
    if "TotalCounter" in properties:
        updates["counter"] = properties["TotalCounter"]
    if "ActualCounter" in properties:
        updates["pulses"] = properties["ActualCounter"]
    if "SensorValue" in properties:
        updates["cur"] = properties["SensorValue"]
    if "Unit" in properties and isinstance(channel, ButtonCounter):
        updates["Unit"] = properties["Unit"]
    return updates


def map_module_properties(module: Module, properties: dict[str, Any]) -> dict[str, Any]:
    """Map module-level Signum properties onto velbus property keys."""
    updates: dict[str, dict[str, Any]] = {}
    if "LightSensorValue" in properties:
        updates["light_value"] = {"cur": properties["LightSensorValue"]}
    if "Program" in properties:
        prog = properties["Program"]
        if isinstance(prog, str):
            updates["selected_program"] = {"selected_program_str": prog}
        else:
            updates["selected_program"] = {"selected_program": int(prog)}
    return updates
