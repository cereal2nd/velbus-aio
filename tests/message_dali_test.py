"""Unit tests for the DALI and edge-lighting message classes.

A couple of these modules (``edge_set_custom_color`` and
``sensor_settings_request``) register command codes that collide with the
command codes used by live modules.  They are never imported during normal
operation, so importing them here against the global command registry would
raise a double-registration error.  Those two classes are therefore exercised
against a throw-away registry via the ``_fresh_registry`` fixture.
"""

from __future__ import annotations

import importlib
import sys

import pytest

import velbusaio.command_registry as cr
from velbusaio.const import PRIORITY_LOW
import velbusaio.messages  # noqa: F401  # ensure the package is registered in the real registry
from velbusaio.messages.dali_device_settings import (
    DaliDeviceSetting,
    DaliDeviceSettingMsg,
    DeviceType,
    DeviceTypeMsg,
    MemberOfGroupMsg,
)
from velbusaio.messages.dali_device_settings_request import (
    DaliDeviceSettingsRequest,
    DataSource,
)
from velbusaio.messages.edge_set_color import (
    CustomColorPriority,
    SetCustomColorMessage,
    SetEdgeColorMessage,
)


class TestDaliDeviceSettingMsg:
    """Tests for DaliDeviceSettingMsg."""

    def test_populate_unknown_subtype_keeps_bytes(self):
        """Test Populate unknown subtype keeps bytes."""
        msg = DaliDeviceSettingMsg()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x00, 0xAB]))
        assert msg.channel == 1
        assert msg.data == bytes([0xAB])
        assert msg.to_json_basic()["data"] == "ab"

    def test_populate_device_type(self):
        """Test Populate device type."""
        msg = DaliDeviceSettingMsg()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x19, 0x06]))
        assert isinstance(msg.data, DeviceTypeMsg)
        assert msg.data.device_type == DeviceType.LedModule
        assert msg.to_json_basic()["data"]["device_type"] == "LedModule"

    def test_populate_member_of_group(self):
        """Test Populate member of group."""
        msg = DaliDeviceSettingMsg()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x15, 0x03, 0x00]))
        assert isinstance(msg.data, MemberOfGroupMsg)
        assert msg.data.member_of_groups == [0, 1]


class TestDeviceTypeMsg:
    """Tests for the DeviceTypeMsg sub-message."""

    def test_from_data(self):
        """Test From data."""
        sub = DeviceTypeMsg.from_data(bytes([0x06]))
        assert sub.device_type == DeviceType.LedModule

    def test_from_data_invalid_length(self):
        """Test From data invalid length."""
        with pytest.raises(ValueError):
            DeviceTypeMsg.from_data(bytes([0x06, 0x00]))

    def test_to_data(self):
        """Test To data."""
        sub = DeviceTypeMsg(device_type=DeviceType.LedModule)
        assert sub.to_data() == bytes([0x06])


class TestMemberOfGroupMsg:
    """Tests for the MemberOfGroupMsg sub-message."""

    def test_round_trip(self):
        """Test Round trip."""
        sub = MemberOfGroupMsg.from_data(bytes([0x03, 0x00]))
        assert sub.member_of_groups == [0, 1]
        assert sub.to_data() == bytes([0x03, 0x00])

    def test_from_data_invalid_length(self):
        """Test From data invalid length."""
        with pytest.raises(ValueError):
            MemberOfGroupMsg.from_data(bytes([0x03]))


class TestDaliDeviceSettingsRequest:
    """Tests for DaliDeviceSettingsRequest."""

    def test_populate_without_settings(self):
        """Test Populate without settings."""
        msg = DaliDeviceSettingsRequest()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05, 0x00]))
        assert msg.channel == 5
        assert msg.data_source == DataSource.FromMemory
        assert msg.settings is None

    def test_populate_with_settings(self):
        """Test Populate with settings."""
        msg = DaliDeviceSettingsRequest()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05, 0x00, 0x19]))
        assert msg.settings == 0x19

    def test_data_to_binary_all(self):
        """Test Data to binary all."""
        msg = DaliDeviceSettingsRequest()
        msg.channel = 5
        msg.settings = None
        assert msg.data_to_binary() == bytes([0xE7, 5, 0])

    def test_data_to_binary_with_setting(self):
        """Test Data to binary with setting."""
        msg = DaliDeviceSettingsRequest()
        msg.channel = 5
        msg.settings = DaliDeviceSetting.DeviceType
        assert msg.data_to_binary() == bytes([0xE7, 5, 0, 25])


class TestSetEdgeColorMessage:
    """Tests for SetEdgeColorMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SetEdgeColorMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x81, 0x0F, 0x1F]))
        assert msg.apply_background_color is True
        assert msg.custom_color_palette is True
        assert msg.apply_to_left_edge is True
        assert msg.apply_to_bottom_edge is True
        assert msg.color_idx == 31

    def test_data_to_binary_defaults(self):
        """Test Data to binary defaults."""
        msg = SetEdgeColorMessage()
        assert msg.custom_color_priority == CustomColorPriority.LOW_PRIORITY
        assert msg.data_to_binary() == bytes([0xD4, 0x00, 0x00, 0x20])


class TestSetCustomColorMessage:
    """Tests for SetCustomColorMessage."""

    def test_data_to_binary_defaults(self):
        """Test Data to binary defaults."""
        msg = SetCustomColorMessage()
        assert msg.data_to_binary() == bytes([0xD4, 0x00, 127, 0x00, 0x00, 0x00])

    def test_data_to_binary_rgb(self):
        """Test Data to binary rgb."""
        msg = SetCustomColorMessage()
        msg.palette_idx = 3
        msg.white_mode = True
        msg.saturation = 100
        msg.red = 10
        msg.green = 20
        msg.blue = 30
        assert msg.data_to_binary() == bytes([0xD4, 3, 0x80 | 100, 10, 20, 30])


@pytest.fixture
def _fresh_registry():
    """Swap in a throw-away command registry for colliding, dead modules."""
    orig = cr.commandRegistry
    cr.commandRegistry = cr.CommandRegistry(cr.MODULE_DIRECTORY)
    try:
        yield
    finally:
        cr.commandRegistry = orig
        for name in (
            "velbusaio.messages.edge_set_custom_color",
            "velbusaio.messages.sensor_settings_request",
        ):
            sys.modules.pop(name, None)


def _reimport(module_name):
    """Force the module body (and its @register) to run against the current registry."""
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


@pytest.mark.usefixtures("_fresh_registry")
class TestEdgeSetCustomColor:
    """Tests for EdgeSetCustomColor (isolated registry)."""

    def test_populate(self):
        """Test Populate."""
        mod = _reimport("velbusaio.messages.edge_set_custom_color")
        msg = mod.EdgeSetCustomColor()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05, 0x81, 0x0A, 0x0B, 0x0C]))
        assert msg.pallet == 5
        assert msg.rgb is True
        assert msg.saturation == 1
        assert (msg.red, msg.green, msg.blue) == (0x0A, 0x0B, 0x0C)

    def test_data_to_binary(self):
        """Test Data to binary."""
        mod = _reimport("velbusaio.messages.edge_set_custom_color")
        msg = mod.EdgeSetCustomColor()
        msg.pallet = 5
        msg.rgb = True
        msg.saturation = 1
        msg.red, msg.green, msg.blue = 0x0A, 0x0B, 0x0C
        assert msg.data_to_binary() == bytes([0xD4, 5, 0x81, 0x0A, 0x0B, 0x0C])


@pytest.mark.usefixtures("_fresh_registry")
class TestSensorSettingsRequestMessage:
    """Tests for SensorSettingsRequestMessage (isolated registry)."""

    def test_defaults(self):
        """Test Defaults."""
        mod = _reimport("velbusaio.messages.sensor_settings_request")
        msg = mod.SensorSettingsRequestMessage(0x01)
        assert msg.rtr is True
        assert msg.priority == PRIORITY_LOW

    def test_data_to_binary(self):
        """Test Data to binary."""
        mod = _reimport("velbusaio.messages.sensor_settings_request")
        msg = mod.SensorSettingsRequestMessage(0x01)
        assert msg.data_to_binary() == bytes([])
