import math

import pytest

from velbusaio.channels import Temperature


@pytest.fixture
def temperature_profile(request):
    ramp_up = [20.0000 + n * 1 / 16 for n in range(17)]
    ramp_down = reversed(ramp_up)
    return [*ramp_up, *ramp_down]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "precision",
    [
        1 / 2,
        1 / 16,
    ],
)
async def test_temperature_same_precision(
    temperature_profile: list[float],
    precision: float,
):
    ch = Temperature(None, None, None, False, True, None, None)
    for temp in temperature_profile:
        temp_truncated_to_precision = math.floor(temp / precision) * precision
        await ch.maybe_update_temperature(temp_truncated_to_precision, precision)
        stored_temp = ch._cur
        assert stored_temp <= temp < stored_temp + precision


@pytest.mark.asyncio
async def test_temperature_alternating_precision(
    temperature_profile: list[float],
):
    ch = Temperature(None, None, None, False, True, None, None)
    for temp in temperature_profile:
        for precision in [1 / 2, 1 / 64]:
            temp_truncated_to_precision = math.floor(temp / precision) * precision
            await ch.maybe_update_temperature(temp_truncated_to_precision, precision)

            stored_temp = ch._cur
            stored_temp_truncated_to_precision = (
                math.floor(stored_temp / precision) * precision
            )
            assert (
                stored_temp_truncated_to_precision
                <= temp
                < stored_temp_truncated_to_precision + precision
            )
