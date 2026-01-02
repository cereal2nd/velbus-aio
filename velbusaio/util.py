"""Some common utils."""

from typing import Union

from velbusaio.const import MAXIMUM_MESSAGE_SIZE, MINIMUM_MESSAGE_SIZE


# Copyright (c) 2017 Thomas Delaet
# Copied from python-velbus (https://github.com/thomasdelaet/python-velbus)
def checksum(data: Union[bytes, bytearray]) -> int:
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
        Exception.__init__(self)
        self.value = value

    def __str__(self) -> str:
        return repr(self.value)


class MessageParseException(Exception):
    pass


class BitSet:
    def __init__(self, value: int):
        self._value = value

    def __getitem__(self, idx: int) -> bool:
        if idx > 8 or idx <= 0:
            raise ValueError("The bitSet id is not within expected range 0 < id < 8")
        return bool((1 << idx) & self._value)

    def __setitem__(self, idx: int, value: bool) -> None:
        if idx > 8 or idx <= 0:
            raise ValueError("The bitSet id is not within expected range 0 < id < 8")
        mask = (0xFF ^ (1 << idx)) & self._value
        self._value = mask & (value << idx)

    def __len__(self) -> int:
        return 8  # a bitset represents one byte
