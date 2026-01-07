"""Some common utils."""

from velbusaio.const import MAXIMUM_MESSAGE_SIZE, MINIMUM_MESSAGE_SIZE


# Copyright (c) 2017 Thomas Delaet
# Copied from python-velbus (https://github.com/thomasdelaet/python-velbus)
def checksum(data: bytes | bytearray) -> int:
    """Calculate the checksum of a Velbus message."""
    if len(data) < MINIMUM_MESSAGE_SIZE - 2:
        raise ValueError("The message is shorter then expected")
    if len(data) > MAXIMUM_MESSAGE_SIZE - 2:
        raise ValueError("The message is longer then expected")
    __checksum = 0
    for data_byte in data:
        __checksum += data_byte
    __checksum = -(__checksum % 256) + 256
    return __checksum % 256


class VelbusException(Exception):
    """Velbus Exception."""

    def __init__(self, value):
        """Initialize Velbus Exception with a value."""
        Exception.__init__(self)
        self.value = value

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return repr(self.value)


class MessageParseException(Exception):
    """Message Parse Exception."""


class BitSet:
    """BitSet helper class."""

    def __init__(self, value: int):
        """Initialize BitSet with an integer value."""
        self._value = value

    def __getitem__(self, idx: int) -> bool:
        """Get the boolean value of the bit at the given index."""
        if idx > 8 or idx <= 0:
            raise ValueError("The bitSet id is not within expected range 0 < id < 8")
        return bool((1 << idx) & self._value)

    def __setitem__(self, idx: int, value: bool) -> None:
        """Set the bit at the given index to the boolean value."""
        if idx > 8 or idx <= 0:
            raise ValueError("The bitSet id is not within expected range 0 < id < 8")
        mask = (0xFF ^ (1 << idx)) & self._value
        self._value = mask & (value << idx)

    def __len__(self) -> int:
        """Return the length of the BitSet (always 8)."""
        return 8  # a bitset represents one byte
