import pytest

from velbusaio.module import Module


@pytest.mark.parametrize(
    ("serial", "expected"),
    [
        # the bus reports the serial as an int (struct.unpack of the module type message)
        (12345, "12345"),
        # a serial of 0 is a valid value, it must not be dropped
        (0, "0"),
        # a vlp file reports the serial as a str, it should be passed through as is
        ("0A1B2C", "0A1B2C"),
        # an unknown serial stays None
        (None, None),
    ],
)
def test_module_serial_is_normalized(serial, expected):
    m = Module(1, 0x0E, serial=serial)

    assert m.get_serial() == expected
    assert m.serial == expected
    if expected is not None:
        assert isinstance(m.get_serial(), str)


def test_module_factory_serial_is_normalized():
    m = Module.factory(1, 0x0E, 12345)

    assert m.get_serial() == "12345"
