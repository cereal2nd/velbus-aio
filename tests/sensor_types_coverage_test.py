"""Every item with category 'sensor' must expose consistent sensor type keys."""

from __future__ import annotations

import pytest

from velbusaio.channels import ButtonCounter, SensorNumber, Temperature
from velbusaio.const import (
    ENERGY_KILO_WATT_HOUR,
    VOLUME_CUBIC_METER_HOUR,
    VOLUME_LITERS_HOUR,
)
from velbusaio.properties import (
    BusErrorOff,
    BusErrorRx,
    BusErrorTx,
    LightValue,
    MemoText,
    PSUCurrent,
    PSULoad,
    PSUPower,
    PSUVoltage,
    SelectedProgram,
)


class TestSensorCategoryItems:
    """Channels and properties that appear in get_all_sensor()."""

    @pytest.mark.parametrize(
        ("factory", "expected_types"),
        [
            (
                lambda m, w: Temperature(m, 1, "T", False, True, w, 0x01),
                ["temperature"],
            ),
            (
                lambda m, w: SensorNumber(m, 1, "N", False, True, w, 0x01),
                ["measurement"],
            ),
            (
                lambda m, w: LightValue(m, "Lux", w),
                ["measurement"],
            ),
            (
                lambda m, w: PSUVoltage(m, "V", w),
                ["voltage"],
            ),
            (
                lambda m, w: PSUCurrent(m, "A", w),
                ["current"],
            ),
            (
                lambda m, w: PSUPower(m, "P", w),
                ["power"],
            ),
            (
                lambda m, w: PSULoad(m, "L", w),
                ["load"],
            ),
            (
                lambda m, w: BusErrorTx(m, "Tx", w),
                ["measurement"],
            ),
            (
                lambda m, w: BusErrorRx(m, "Rx", w),
                ["measurement"],
            ),
            (
                lambda m, w: BusErrorOff(m, "Off", w),
                ["measurement"],
            ),
        ],
    )
    def test_single_entity_sensor_types(
        self,
        mock_module,
        mock_writer,
        factory,
        expected_types,
    ):
        item = factory(mock_module, mock_writer)
        assert "sensor" in item.get_categories()
        assert item.get_sensor_types() == expected_types

    @pytest.mark.parametrize(
        ("unit", "expected"),
        [
            (VOLUME_CUBIC_METER_HOUR, ["flow", "gas"]),
            (VOLUME_LITERS_HOUR, ["flow", "water"]),
            (ENERGY_KILO_WATT_HOUR, ["power", "energy"]),
        ],
    )
    def test_button_counter_sensor_types(
        self, mock_module, mock_writer, unit, expected
    ):
        button = ButtonCounter(
            mock_module, 1, "Counter", False, True, mock_writer, 0x01
        )
        button._counter = 1
        button._Unit = unit
        assert button.get_sensor_types() == expected

    def test_non_sensor_items_return_empty_types(self, mock_module, mock_writer):
        """Items without the sensor category are not sensor entities."""
        memo = MemoText(mock_module, "Memo", mock_writer)
        program = SelectedProgram(mock_module, "Prog", mock_writer)
        assert memo.get_categories() == []
        assert program.get_categories() == ["select"]
        assert memo.get_sensor_types() == []
        assert program.get_sensor_types() == []
