"""Derive Velbus config panel UI schema from module specifications."""

from __future__ import annotations

import importlib.resources
import json
from typing import TYPE_CHECKING, Any

from velbusaio.actions import iter_action_options
from velbusaio.channels import Button, Relay

if TYPE_CHECKING:
    from velbusaio.module import Module

_SPEC_CACHE: dict[int, dict[str, Any]] = {}


def load_module_spec(type_id: int) -> dict[str, Any]:
    """Load and cache the merged module specification for a type id."""
    if type_id in _SPEC_CACHE:
        return _SPEC_CACHE[type_id]

    global_data: dict[str, Any] = {}
    global_path = importlib.resources.files("velbusaio").joinpath(
        "module_spec/global.json"
    )
    if global_path.is_file():
        global_data = json.loads(global_path.read_text(encoding="utf-8"))

    spec_path = importlib.resources.files("velbusaio").joinpath(
        f"module_spec/{type_id:02X}.json"
    )
    if not spec_path.is_file():
        spec: dict[str, Any] = {}
    else:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))

    for key, value in global_data.items():
        if key not in spec:
            spec[key] = value
        elif isinstance(value, dict) and isinstance(spec[key], dict):
            spec[key] = {**value, **spec[key]}

    _SPEC_CACHE[type_id] = spec
    return spec


def _channel_entries(spec: dict[str, Any]) -> list[dict[str, Any]]:
    channels = spec.get("Channels", {})
    enable_channels = {
        int(key)
        for key in spec.get("Memory", {}).get("ChannelEnable", {}).get("channels", {})
    }
    entries: list[dict[str, Any]] = []
    for chan_key, chan_data in sorted(channels.items(), key=lambda item: int(item[0])):
        channel = int(chan_key)
        entries.append(
            {
                "channel": channel,
                "name": chan_data.get("Name", f"Channel {channel}"),
                "type": chan_data.get("Type"),
                "editable": chan_data.get("Editable") == "yes",
                "subdevice": chan_data.get("Subdevice") == "yes",
                "supports_enable": channel in enable_channels,
            }
        )
    return entries


def _channel_enable_section(spec: dict[str, Any]) -> dict[str, Any] | None:
    enable = spec.get("Memory", {}).get("ChannelEnable")
    if not enable:
        return None
    channels = sorted(int(key) for key in enable.get("channels", {}))
    if not channels:
        return None
    return {
        "id": "channel_enable",
        "type": "channel_enable",
        "channels": channels,
    }


def _contact_section(spec: dict[str, Any]) -> dict[str, Any] | None:
    action_table = spec.get("Memory", {}).get("ActionTable")
    if not action_table:
        return None
    channels = sorted(
        int(key)
        for key, chan_spec in action_table.get("channels", {}).items()
        if isinstance(chan_spec, dict) and chan_spec.get("noc_address") is not None
    )
    if not channels:
        return None
    return {
        "id": "contact",
        "type": "contact",
        "channels": channels,
        "options": ["NO", "NC"],
    }


def _editable_name_channels(spec: dict[str, Any]) -> list[dict[str, Any]]:
    memory_channels = spec.get("Memory", {}).get("Channels", {})
    editable = {
        int(chan_key)
        for chan_key, chan_data in spec.get("Channels", {}).items()
        if chan_data.get("Editable") == "yes" and chan_key in memory_channels
    }
    return [entry for entry in _channel_entries(spec) if entry["channel"] in editable]


def _action_table_section(spec: dict[str, Any]) -> dict[str, Any] | None:
    action_table = spec.get("Memory", {}).get("ActionTable")
    if not action_table:
        return None
    catalog_id = str(action_table.get("actions", "relay_classic"))
    channels = sorted(int(key) for key in action_table.get("channels", {}))
    kind = str(
        action_table.get("kind")
        or ("input" if catalog_id.startswith("input_") else "output")
    )
    return {
        "id": "action_table",
        "type": "action_table",
        "kind": kind,
        "catalog_id": catalog_id,
        "slot_count": int(action_table.get("slot_count", 39)),
        "slot_size": int(action_table.get("slot_size", 6)),
        "layout": action_table.get("layout", "per_channel"),
        "channels": channels,
        "actions": list(iter_action_options(catalog_id)),
    }


def _properties_section(spec: dict[str, Any]) -> dict[str, Any] | None:
    properties = spec.get("Properties", {})
    if not properties:
        return None
    items: list[dict[str, Any]] = []
    for key, prop_data in properties.items():
        if "Type" not in prop_data:
            continue
        items.append(
            {
                "key": key,
                "name": prop_data.get("Name", key),
                "property_type": prop_data["Type"],
            }
        )
    if not items:
        return None
    return {"id": "properties", "type": "properties", "properties": items}


def get_module_type_schema(type_id: int) -> dict[str, Any]:
    """Return the panel schema for a module type."""
    spec = load_module_spec(type_id)
    sections: list[dict[str, Any]] = []

    channels = _channel_entries(spec)
    if channels:
        sections.append({"id": "channels", "type": "channels", "channels": channels})

    name_channels = _editable_name_channels(spec)
    if name_channels:
        sections.append(
            {
                "id": "channel_names",
                "type": "channel_names",
                "channels": name_channels,
            }
        )

    contact_section = _contact_section(spec)
    if contact_section is not None:
        sections.append(contact_section)

    enable_section = _channel_enable_section(spec)
    if enable_section is not None:
        sections.append(enable_section)

    action_section = _action_table_section(spec)
    if action_section is not None:
        sections.append(action_section)

    properties_section = _properties_section(spec)
    if properties_section is not None:
        sections.append(properties_section)

    panel_override = spec.get("Panel", {})
    if order := panel_override.get("section_order"):
        order_map = {section["id"]: index for index, section in enumerate(order)}
        sections.sort(key=lambda section: order_map.get(section["id"], len(order_map)))

    return {
        "type_id": type_id,
        "type_name": spec.get("Type", f"0x{type_id:02X}"),
        "sections": sections,
    }


async def get_module_instance_data(
    module: Module, *, refresh: bool = False
) -> dict[str, Any]:
    """Return live module values for the config panel."""
    if not refresh:
        await module.ensure_panel_metadata_cache()
    channels = module.get_channels()
    channel_data: dict[str, Any] = {}
    for channel_num, channel in channels.items():
        entry: dict[str, Any] = {
            "name": channel.get_name(),
            "type": type(channel).__name__,
        }
        if isinstance(channel, Button) and channel.supports_channel_enable():
            entry["enabled"] = await channel.get_channel_enabled(refresh=refresh)
        elif hasattr(channel, "is_enabled"):
            entry["enabled"] = channel.is_enabled()
        table = (
            channel.get_action_table() if hasattr(channel, "get_action_table") else None
        )
        if (
            isinstance(channel, Relay)
            and table is not None
            and table.noc_address is not None
        ):
            normal_closed = await channel.get_normal_closed(refresh=refresh)
            if normal_closed is not None:
                entry["contact"] = "NC" if normal_closed else "NO"
        channel_data[str(channel_num)] = entry

    properties: dict[str, Any] = {}
    for key, prop in module.get_properties().items():
        if hasattr(prop, "get_selected_program"):
            properties[key] = prop.get_selected_program()
        elif hasattr(prop, "get_state"):
            properties[key] = prop.get_state()

    return {
        "address": module.get_addresses()[0],
        "name": module.get_name(),
        "type_id": module.get_type(),
        "type_name": module.get_type_name(),
        "serial": module.get_serial(),
        "sw_version": module.get_sw_version(),
        "channels": channel_data,
        "properties": properties,
    }
