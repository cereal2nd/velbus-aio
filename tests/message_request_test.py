"""Unit tests for the request/simple command message classes."""

from __future__ import annotations

import pytest

from velbusaio.const import PRIORITY_HIGH, PRIORITY_LOW
from velbusaio.message import ParserError
from velbusaio.messages.bus_active import BusActiveMessage
from velbusaio.messages.bus_error_counter_status_request import (
    BusErrorStatusRequestMessage,
)
from velbusaio.messages.bus_off import BusOffMessage
from velbusaio.messages.channel_name_request import (
    ChannelNameRequestMessage,
    ChannelNameRequestMessage2,
    ChannelNameRequestMessage3,
)
from velbusaio.messages.counter_status_request import CounterStatusRequestMessage
from velbusaio.messages.interface_status_request import InterfaceStatusRequestMessage
from velbusaio.messages.light_value_request import LightValueRequest
from velbusaio.messages.memory_dump_request import MemoryDumpRequestMessage
from velbusaio.messages.module_status_request import ModuleStatusRequestMessage
from velbusaio.messages.module_type_request import ModuleTypeRequestMessage
from velbusaio.messages.realtime_clock_status_request import RealtimeClockStatusRequest
from velbusaio.messages.receive_buffer_full import ReceiveBufferFullMessage
from velbusaio.messages.receive_ready import ReceiveReadyMessage
from velbusaio.messages.sensor_temp_request import (
    TEMP_AUTOSEND_DISABLED,
    TEMP_AUTOSEND_ON_CHANGE,
    SensorTempRequest,
)
from velbusaio.messages.temp_sensor_settings_part1 import TempSensorSettingsPart1
from velbusaio.messages.temp_sensor_settings_part2 import TempSensorSettingsPart2
from velbusaio.messages.temp_sensor_settings_part3 import TempSensorSettingsPart3
from velbusaio.messages.temp_sensor_settings_part4 import TempSensorSettingsPart4
from velbusaio.messages.temp_sensor_settings_request import TempSensorSettingsRequest


class TestBusActiveMessage:
    """Tests for BusActiveMessage."""

    def test_default_high_priority(self):
        """Test Default high priority."""
        assert BusActiveMessage(0x01).priority == PRIORITY_HIGH

    def test_populate(self):
        """Test Populate."""
        msg = BusActiveMessage()
        msg.populate(PRIORITY_HIGH, 0x01, False, bytes([]))
        assert msg.address == 0x01

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert BusActiveMessage().data_to_binary() == bytes([0x0A])


class TestBusOffMessage:
    """Tests for BusOffMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = BusOffMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([]))
        assert msg.address == 0x01

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert BusOffMessage().data_to_binary() == bytes([0x09])


class TestBusErrorStatusRequestMessage:
    """Tests for BusErrorStatusRequestMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert BusErrorStatusRequestMessage().data_to_binary() == bytes([0xD9])


class TestInterfaceStatusRequestMessage:
    """Tests for InterfaceStatusRequestMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert InterfaceStatusRequestMessage().data_to_binary() == bytes([0x0E])

    def test_populate_rejects_data(self):
        """Test Populate rejects data."""
        msg = InterfaceStatusRequestMessage()
        with pytest.raises(ParserError):
            msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]))


class TestMemoryDumpRequestMessage:
    """Tests for MemoryDumpRequestMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert MemoryDumpRequestMessage().data_to_binary() == bytes([0xCB])


class TestRealtimeClockStatusRequest:
    """Tests for RealtimeClockStatusRequest."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert RealtimeClockStatusRequest().data_to_binary() == bytes([0xD7])


class TestSensorTempRequest:
    """Tests for SensorTempRequest."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert SensorTempRequest().data_to_binary() == bytes([0xE5])

    def test_data_to_binary_disabled(self):
        """Test autosend disabled ('never')."""
        msg = SensorTempRequest(0x10, TEMP_AUTOSEND_DISABLED)
        assert msg.data_to_binary() == bytes([0xE5, 0x01])

    def test_data_to_binary_on_change(self):
        """Test autosend on temperature change."""
        msg = SensorTempRequest(0x10, TEMP_AUTOSEND_ON_CHANGE)
        assert msg.data_to_binary() == bytes([0xE5, 0x05])

    def test_data_to_binary_fixed_interval(self):
        """Test autosend with a fixed interval in seconds."""
        msg = SensorTempRequest(0x10, 60)
        assert msg.data_to_binary() == bytes([0xE5, 60])


class TestLightValueRequest:
    """Tests for LightValueRequest."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert LightValueRequest().data_to_binary() == bytes([0xAA])


class TestReceiveBufferFullMessage:
    """Tests for ReceiveBufferFullMessage."""

    def test_default_high_priority(self):
        """Test Default high priority."""
        assert ReceiveBufferFullMessage(0x01).priority == PRIORITY_HIGH

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert ReceiveBufferFullMessage().data_to_binary() == bytes([0x0B])


class TestReceiveReadyMessage:
    """Tests for ReceiveReadyMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert ReceiveReadyMessage().data_to_binary() == bytes([0x0C])


class TestTempSensorSettingsRequest:
    """Tests for TempSensorSettingsRequest."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert TempSensorSettingsRequest().data_to_binary() == bytes([0xE7])


class TestTempSensorSettingsParts:
    """Tests for TempSensorSettingsPart1..4."""

    @pytest.mark.parametrize(
        ("cls", "code"),
        [
            (TempSensorSettingsPart1, 0xE8),
            (TempSensorSettingsPart2, 0xE9),
            (TempSensorSettingsPart3, 0xC6),
            (TempSensorSettingsPart4, 0xB9),
        ],
    )
    def test_data_to_binary(self, cls, code):
        """Test Data to binary."""
        assert cls().data_to_binary() == bytes([code])


class TestModuleStatusRequestMessage:
    """Tests for ModuleStatusRequestMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ModuleStatusRequestMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x03]))
        assert msg.channels == [1, 2]

    def test_data_to_binary_list(self):
        """Test Data to binary list."""
        msg = ModuleStatusRequestMessage()
        msg.channels = [1, 2]
        assert msg.data_to_binary() == bytes([0xFA, 0x03])

    def test_data_to_binary_str(self):
        """Test Data to binary str."""
        msg = ModuleStatusRequestMessage()
        msg.channels = "FF"
        assert msg.data_to_binary() == bytes([0xFA, 0xFF])


class TestModuleTypeRequestMessage:
    """Tests for ModuleTypeRequestMessage."""

    def test_defaults_rtr(self):
        """Test Defaults rtr."""
        msg = ModuleTypeRequestMessage(0x01)
        assert msg.rtr is True
        assert msg.priority == PRIORITY_LOW

    def test_populate(self):
        """Test Populate."""
        msg = ModuleTypeRequestMessage()
        msg.populate(PRIORITY_LOW, 0x01, True, bytes([]))
        assert msg.address == 0x01

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert ModuleTypeRequestMessage().data_to_binary() == bytes([])


class TestChannelNameRequestMessage:
    """Tests for ChannelNameRequestMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNameRequestMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x03]))
        assert msg.channels == [1, 2]

    def test_data_to_binary_list(self):
        """Test Data to binary list."""
        msg = ChannelNameRequestMessage()
        msg.channels = [1, 2]
        assert msg.data_to_binary() == bytes([0xEF, 0x03])

    def test_data_to_binary_non_list(self):
        """Test Data to binary non list."""
        msg = ChannelNameRequestMessage()
        msg.channels = "all"
        assert msg.data_to_binary() == bytes([0xEF, 0xFF])


class TestChannelNameRequestMessage2:
    """Tests for ChannelNameRequestMessage2 (VMB2BL)."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNameRequestMessage2()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x06]))
        assert msg.channels == [1, 2]

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ChannelNameRequestMessage2()
        msg.channels = [1, 2]
        assert msg.data_to_binary() == bytes([0xEF, 0x0F])


class TestChannelNameRequestMessage3:
    """Tests for ChannelNameRequestMessage3 (VMBDALI)."""

    def test_populate(self):
        """Test Populate."""
        msg = ChannelNameRequestMessage3()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x05]))
        assert msg.channels == 5

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ChannelNameRequestMessage3()
        msg.channels = 5
        assert msg.data_to_binary() == bytes([0xEF, 5])


class TestCounterStatusRequestMessage:
    """Tests for CounterStatusRequestMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = CounterStatusRequestMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x00, 0x00]))
        assert msg.address == 0x01

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = CounterStatusRequestMessage()
        msg.channels = [1]
        assert msg.data_to_binary() == bytes([0xBD, 0x01, 0x00])
