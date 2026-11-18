"""Tests for Signum property and module type mapping."""

from __future__ import annotations

from velbusaio.channels import Dimmer, Relay
from velbusaio.bus.manager.mapping import (
    map_module_properties,
    map_properties_to_update,
    parse_build_number,
    remap_channel_number,
    manager_module_type_to_code,
)


def test_manager_module_type_to_code() -> None:
    assert manager_module_type_to_code("VMB1RY") == 0x02
    assert manager_module_type_to_code("VMB4RYLD_20") == 0x26


def test_parse_build_number() -> None:
    assert parse_build_number(1247) == (12, 47)
    assert parse_build_number("1247") == (12, 47)


def test_map_relay_on() -> None:
    relay = Relay(
        module=None,  # type: ignore[arg-type]
        num=1,
        name="r",
        nameEditable=False,
        subDevice=False,
        writer=lambda m: None,  # type: ignore[arg-type, assignment]
        address=5,
    )
    updates = map_properties_to_update(relay, {"On": True})
    assert updates["on"] is True


def test_map_dimmer_brightness() -> None:
    dimmer = Dimmer(
        module=None,  # type: ignore[arg-type]
        num=1,
        name="d",
        nameEditable=False,
        subDevice=False,
        writer=lambda m: None,  # type: ignore[arg-type, assignment]
        address=5,
        slider_scale=100,
    )
    updates = map_properties_to_update(dimmer, {"Brightness": 50})
    assert updates["state"] == 50


def test_remap_default_identity() -> None:
    assert remap_channel_number(0x02, 3) == 3


def test_map_module_light_sensor_value() -> None:
    """Signum LightSensorValue maps to velbus spec key light_value."""
    updates = map_module_properties(
        module=None,  # type: ignore[arg-type]
        properties={"LightSensorValue": 123},
    )
    assert updates == {"light_value": {"cur": 123}}
