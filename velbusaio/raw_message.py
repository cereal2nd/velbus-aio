import binascii
import logging
from typing import NamedTuple, Optional

from velbusaio.const import (
    END_BYTE,
    HEADER_LENGTH,
    MAXIMUM_MESSAGE_SIZE,
    MINIMUM_MESSAGE_SIZE,
    NO_RTR,
    PRIORITIES,
    RTR,
    START_BYTE,
    TAIL_LENGTH,
)
from velbusaio.util import checksum
from velbusaio.util import checksum as calculate_checksum


class RawMessage(NamedTuple):
    priority: int
    address: int
    rtr: bool
    data: bytes

    @property
    def command(self) -> Optional[int]:
        return self.data[0] if len(self.data) > 0 else None

    @property
    def data_only(self) -> Optional[bytes]:
        return self.data[1:] if len(self.data) > 1 else None

    def to_bytes(self) -> bytes:
        # create header:
        header_bytes = bytes(
            [
                START_BYTE,
                self.priority,
                self.address,
                (RTR if self.rtr else NO_RTR) | len(self.data),
            ]
        )

        tail_bytes = bytes([checksum(header_bytes + self.data), END_BYTE])

        return header_bytes + self.data + tail_bytes

    def __repr__(self) -> str:
        return (
            f"RawMessage(priority={self.priority:02x}, address={self.address:02x},"
            f" rtr={self.rtr!r}, command={self.command},"
            f" data={binascii.hexlify(self.data, ' ')})"
        )


def create(rawmessage: bytearray) -> tuple[Optional[RawMessage], bytearray]:
    rawmessage = _trim_buffer_garbage(rawmessage)

    while True:
        if len(rawmessage) < MINIMUM_MESSAGE_SIZE:
            logging.debug("Buffer does not yet contain a full message")
            return None, rawmessage

        try:
            return _parse(rawmessage)
        except ParseError:
            logging.error(
                f"Could not parse the message {binascii.hexlify(rawmessage)}. Truncating invalid data."
            )
            rawmessage = _trim_buffer_garbage(
                rawmessage[1:]
            )  # try to find possible start of a message


class ParseError(Exception):
    pass


def _parse(rawmessage: bytearray) -> tuple[Optional[RawMessage], bytearray]:
    if len(rawmessage) < MINIMUM_MESSAGE_SIZE or len(rawmessage) > MAXIMUM_MESSAGE_SIZE:
        raise ValueError("Received a raw message with an illegal lemgth")
    if rawmessage[0] != START_BYTE:
        raise ValueError("Received a raw message with the wrong startbyte")

    priority = rawmessage[1]
    if priority not in PRIORITIES:
        raise ParseError(
            f"Invalid priority byte: {priority:02x} in {binascii.hexlify(rawmessage)}"
        )

    address = rawmessage[2]

    rtr = rawmessage[3] & RTR == RTR  # high nibble of the 4th byte
    data_size = rawmessage[3] & 0x0F  # low nibble of the 4th byte

    if HEADER_LENGTH + data_size + TAIL_LENGTH > len(rawmessage):
        return (
            None,
            rawmessage,
        )  # the full package is not available in the current buffer

    if rawmessage[HEADER_LENGTH + data_size + 1] != END_BYTE:
        raise ParseError(f"Invalid end byte in {binascii.hexlify(rawmessage)}")

    checksum = rawmessage[HEADER_LENGTH + data_size]

    calculated_checksum = calculate_checksum(rawmessage[: HEADER_LENGTH + data_size])

    if calculated_checksum != checksum:
        raise ParseError(
            f"Invalid checksum: expected {calculated_checksum:02x},"
            f" but got {checksum:02x} in {binascii.hexlify(rawmessage)}"
        )

    data = bytes(rawmessage[HEADER_LENGTH : HEADER_LENGTH + data_size])

    return (
        RawMessage(priority, address, rtr, data),
        rawmessage[HEADER_LENGTH + data_size + TAIL_LENGTH :],
    )


def _trim_buffer_garbage(rawmessage: bytearray) -> bytearray:
    """Remove leading garbage bytes from a byte stream."""

    # A proper message byte stream begins with 0x0F.
    if rawmessage and rawmessage[0] != START_BYTE:
        start_index = rawmessage.find(START_BYTE)
        if start_index > -1:
            #           logging.debug(
            #                "Trimming leading garbage from buffer content: {buffer} becomes {new_buffer}".format(
            #                    buffer=binascii.hexlify(rawmessage),
            #                    new_buffer=binascii.hexlify(rawmessage[start_index:]),
            #                )
            #            )
            return rawmessage[start_index:]
        logging.debug(
            f"Trimming whole buffer as it does not contain the start byte: {binascii.hexlify(rawmessage)}"
        )
        return []

    return rawmessage
