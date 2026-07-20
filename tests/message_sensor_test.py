"""Unit tests for sensor and temperature setpoint message classes."""

from __future__ import annotations

from velbusaio.const import PRIORITY_LOW
from velbusaio.messages.raw import MeteoRawMessage, SensorRawMessage
from velbusaio.messages.sensor_temperature import SensorTemperatureMessage
from velbusaio.messages.set_temperature import SetTemperatureMessage
from velbusaio.messages.temp_set_cooling import TempSetCoolingMessage
from velbusaio.messages.temp_set_heating import TempSetHeatingMessage


class TestSensorTemperatureMessage:
    """Tests for SensorTemperatureMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SensorTemperatureMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x02, 0x00, 0x01, 0x00, 0x03, 0x00])
        )
        assert msg.getCurTemp() == 1.0
        assert msg.getMinTemp() == 0.5
        assert msg.getMaxTemp() == 1.5

    def test_negative_temperature(self):
        """Test Negative temperature."""
        msg = SensorTemperatureMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x80, 0x00, 0x00, 0x00, 0x00, 0x00])
        )
        assert msg.cur < 0


class TestMeteoRawMessage:
    """Tests for MeteoRawMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = MeteoRawMessage()
        msg.populate(
            PRIORITY_LOW, 0x01, False, bytes([0x00, 0x20, 0x00, 0x20, 0x00, 0x20])
        )
        assert msg.rain == 0.1
        assert msg.light == 1.0
        assert msg.wind == 0.1


class TestSensorRawMessage:
    """Tests for SensorRawMessage."""

    def test_populate_millivolt(self):
        """Test Populate millivolt."""
        msg = SensorRawMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x01, 0x00, 0x00, 0x00, 0x64]))
        assert msg.sensor == 1
        assert msg.mode == 0
        assert msg.value == 25.0
        assert msg.unit == "mV"

    def test_populate_microamp(self):
        """Test Populate microamp."""
        msg = SensorRawMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x02, 0x01, 0x00, 0x00, 0x0A]))
        assert msg.value == 50
        assert msg.unit == "µA"


class TestSetTemperatureMessage:
    """Tests for SetTemperatureMessage."""

    def test_populate(self):
        """Test Populate."""
        msg = SetTemperatureMessage()
        msg.populate(PRIORITY_LOW, 0x01, False, bytes([0x00, 0x0A]))
        assert msg.temp_type == 0
        assert msg.temp == 20

    def test_data_to_binary(self):
        """Test Data to binary."""
        msg = SetTemperatureMessage()
        msg.temp_type = 0
        msg.temp = 20
        assert msg.data_to_binary() == bytes([0xE4, 0, 20])


class TestTempSetCoolingMessage:
    """Tests for TempSetCoolingMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert TempSetCoolingMessage().data_to_binary() == bytes([0xDF, 0xAA])


class TestTempSetHeatingMessage:
    """Tests for TempSetHeatingMessage."""

    def test_data_to_binary(self):
        """Test Data to binary."""
        assert TempSetHeatingMessage().data_to_binary() == bytes([0xE0, 0xAA])
