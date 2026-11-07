"""Shared helpers for 0xBE counter / kWh status payload fields."""


def compute_counter_kwh_watt(
    counter: int, pulses: int, delay: int
) -> tuple[float, float]:
    """Derive total kWh and instantaneous watts from a counter status frame."""
    if not pulses:
        return 0.0, 0.0
    kwh = float(counter) / pulses
    if not delay or delay == 0xFFFF:
        return kwh, 0.0
    watt = float((1000 * 1000 * 3600) / (delay * pulses))
    if watt < 55:
        watt = 0.0
    return kwh, watt
