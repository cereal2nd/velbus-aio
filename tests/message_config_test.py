"""Unit tests for configuration, type and memory message classes."""

from __future__ import annotations

from velbusaio.const import PRIORITY_FIRMWARE, PRIORITY_LOW
from velbusaio.messages.memory_data import MemoryDataMessage
from velbusaio.messages.memory_data_block import MemoryDataBlockMessage
from velbusaio.messages.module_subtype import ModuleSubTypeMessage
from velbusaio.messages.module_type import ModuleType2Message, ModuleTypeMessage
from velbusaio.messages.read_data_block_from_memory import (
    ReadDataBlockFromMemoryMessage,
)
from velbusaio.messages.read_data_from_memory import ReadDataFromMemoryMessage
from velbusaio.messages.select_program import SelectProgramMessage
from velbusaio.messages.set_date import SetDate
from velbusaio.messages.set_daylight_saving import SetDaylightSaving
from velbusaio.messages.set_realtime_clock import SetRealtimeClock
from velbusaio.messages.write_data_to_memory import WriteDataToMemoryMessage
from velbusaio.messages.write_memory_block import WriteMemoryBlockMessage
from velbusaio.messages.write_module_address_and_serial_number import (
    WriteModuleAddressAndSerialNumberMessage,
)


class TestModuleTypeMessage:
    """Tests for ModuleTypeMessage."""

    def test_populate_with_serial(self):
        """Test Populate with serial."""
        msg = ModuleTypeMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x20, 0x12, 0x34, 0x01, 0x18, 0x2A])
        )
        assert msg.module_type == 0x20
        assert msg.serial == 0x1234
        assert msg.memory_map_version == 1
        assert msg.build_year == 0x18
        assert msg.build_week == 0x2A
        assert msg.module_type_name() == "VMBGP4"

    def test_populate_without_serial(self):
        """Test Populate without serial."""
        msg = ModuleTypeMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x03, 0x18, 0x2A]))
        assert msg.module_type == 0x03
        assert msg.serial == 0
        assert msg.module_type_name() == "VMB1BL"

    def test_unknown_module(self):
        """Test Unknown module."""
        msg = ModuleTypeMessage()
        msg.module_type = 0xFE
        assert msg.module_type_name() == "Unknown"


class TestModuleType2Message:
    """Tests for ModuleType2Message."""

    def test_populate(self):
        """Test Populate."""
        msg = ModuleType2Message()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x20, 0x12, 0x34, 0x01, 0x18, 0x2A, 0x01])
        )
        assert msg.module_type == 0x20
        assert msg.serial == 0x1234
        assert msg.memory_map_version == 1
        assert msg.build_year == 0x18
        assert msg.build_week == 0x2A
        assert msg.term == 1
        assert msg.module_name() == "Unknown"


class TestModuleSubTypeMessage:
    """Tests for ModuleSubTypeMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ModuleSubTypeMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x20, 0x12, 0x34, 0xF1, 0xF2, 0xF3, 0xF4])
        )
        assert msg.module_type == 0x20
        assert msg.serial == 0x1234
        assert msg.sub_address_1 == 0xF1
        assert msg.sub_address_2 == 0xF2
        assert msg.sub_address_3 == 0xF3
        assert msg.sub_address_4 == 0xF4
        assert msg.module_name() == "Unknown"


class TestSetDate:
    """Tests for SetDate."""

    def test_populate(self):
        """Test Populate."""
        msg = SetDate()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x0F, 0x06, 0x07, 0xE9]))
        assert msg._day == 15
        assert msg._mon == 6
        assert msg._year == 2025

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SetDate(0x01, day=15, mon=6, year=2025)
        assert msg.data_to_binary() == bytes([0xB7, 15, 6, 0x07, 0xE9])


class TestSetDaylightSaving:
    """Tests for SetDaylightSaving."""

    def test_populate(self):
        """Test Populate."""
        msg = SetDaylightSaving()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01]))
        assert msg._ds == 1

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SetDaylightSaving(0x01, ds=1)
        assert msg.data_to_binary() == bytes([0xAF, 1])


class TestSetRealtimeClock:
    """Tests for SetRealtimeClock."""

    def test_populate(self):
        """Test Populate."""
        msg = SetRealtimeClock()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x02, 0x0C, 0x1E]))
        assert msg._wday == 2
        assert msg._hour == 12
        assert msg._min == 30

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SetRealtimeClock(0x01, wday=2, hour=12, min=30)
        assert msg.data_to_binary() == bytes([0xD8, 2, 12, 30])


class TestSelectProgramMessage:
    """Tests for SelectProgramMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SelectProgramMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x02]))
        assert msg.select_program == 2

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SelectProgramMessage(program=1)
        assert msg.data_to_binary() == bytes([0xB3, 1])


class TestWriteDataToMemoryMessage:
    """Tests for WriteDataToMemoryMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = WriteDataToMemoryMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x03]))
        assert msg.high_address == 1
        assert msg.low_address == 2
        assert msg.data == 3

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = WriteDataToMemoryMessage()
        msg.high_address = 1
        msg.low_address = 2
        msg.data = 3
        assert msg.data_to_binary() == bytes([0xFC, 1, 2, 3])


class TestWriteMemoryBlockMessage:
    """Tests for WriteMemoryBlockMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = WriteMemoryBlockMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x0A, 0x0B, 0x0C, 0x0D])
        )
        assert msg.high_address == 1
        assert msg.low_address == 2
        assert msg.data == bytes([0x0A, 0x0B, 0x0C, 0x0D])

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = WriteMemoryBlockMessage()
        msg.high_address = 1
        msg.low_address = 2
        msg.data = bytes([0x0A, 0x0B, 0x0C, 0x0D])
        assert msg.data_to_binary() == bytes([0xCA, 1, 2, 0x0A, 0x0B, 0x0C, 0x0D])


class TestMemoryDataMessage:
    """Tests for MemoryDataMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = MemoryDataMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x03]))
        assert msg.high_address == 1
        assert msg.low_address == 2
        assert msg.data == 3

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = MemoryDataMessage()
        msg.high_address = 1
        msg.low_address = 2
        msg.data = 3
        assert msg.data_to_binary() == bytes([0xFE, 1, 2, 3])


class TestMemoryDataBlockMessage:
    """Tests for MemoryDataBlockMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = MemoryDataBlockMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x01, 0x02, 0x0A, 0x0B, 0x0C, 0x0D])
        )
        assert msg.high_address == 1
        assert msg.low_address == 2
        assert msg.data == bytes([0x0A, 0x0B, 0x0C, 0x0D])

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = MemoryDataBlockMessage()
        msg.high_address = 1
        msg.low_address = 2
        msg.data = bytes([0x0A, 0x0B, 0x0C, 0x0D])
        assert msg.data_to_binary() == bytes([0xCC, 1, 2, 0x0A, 0x0B, 0x0C, 0x0D])


class TestReadDataFromMemoryMessage:
    """Tests for ReadDataFromMemoryMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ReadDataFromMemoryMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x0A, 0x0B]))
        assert msg.high_address == 0x0A
        assert msg.low_address == 0x0B

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ReadDataFromMemoryMessage()
        msg.high_address = 0x0A
        msg.low_address = 0x0B
        assert msg.data_to_binary() == bytes([0xFD, 0x0A, 0x0B])


class TestReadDataBlockFromMemoryMessage:
    """Tests for ReadDataBlockFromMemoryMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = ReadDataBlockFromMemoryMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x0A, 0x0B]))
        assert msg.high_address == 0x0A
        assert msg.low_address == 0x0B

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = ReadDataBlockFromMemoryMessage()
        msg.high_address = 0x0A
        msg.low_address = 0x0B
        assert msg.data_to_binary() == bytes([0xC9, 0x0A, 0x0B])


class TestWriteModuleAddressAndSerialNumberMessage:
    """Tests for WriteModuleAddressAndSerialNumberMessage."""

    def test_defaults(self):
        """Test Defaults."""
        msg = WriteModuleAddressAndSerialNumberMessage(0x01)
        assert msg.priority == PRIORITY_FIRMWARE
        assert msg.rtr is False
        assert msg.module_type == 0x00
        assert msg.address == 0x01
