"""Tests for counter status watt/kWh derivation."""

from velbusaio.messages.counter_rate import compute_counter_kwh_watt


def test_compute_counter_kwh_watt() -> None:
    kwh, watt = compute_counter_kwh_watt(100, 100, 10)
    assert kwh == 1.0
    assert watt == (1000 * 1000 * 3600) / (10 * 100)


def test_compute_counter_watt_below_noise_floor() -> None:
    _, watt = compute_counter_kwh_watt(100, 100, 0xFFFF)
    assert watt == 0.0
