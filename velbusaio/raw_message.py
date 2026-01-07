"""Raw message representation and parsing for Velbus messages."""

import binascii
import logging
from typing import NamedTuple

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
from velbusaio.util import checksum, checksum as calculate_checksum

logger = logging.getLogger(__name__)


class RawMessage(NamedTuple):
    """Raw Velbus message representation."""

    priority: int
    address: int
    rtr: bool
    data: bytes

    @property
    def command(self) -> int | None:
        """Return the command byte of the message."""
        return self.data[0] if len(self.data) > 0 else None

    @property
    def data_only(self) -> bytes | None:
        """Return the data bytes excluding the command byte."""
        return self.data[1:] if len(self.data) > 1 else None

    def to_bytes(self) -> bytes:
        """Convert the RawMessage back to bytes."""
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
        """Return string representation of the RawMessage."""
        return (
            f"RawMessage(priority={self.priority:02x}, address={self.address:02x},"
            f" rtr={self.rtr!r}, command={self.command},"
            f" data={binascii.hexlify(self.data, ' ')})"
        )


def create(rawmessage: bytearray) -> tuple[RawMessage | None, bytearray]:
    """Create a RawMessage from a bytearray buffer."""

    rawmessage = _trim_buffer_garbage(rawmessage)

    while True:
        if len(rawmessage) < MINIMUM_MESSAGE_SIZE:
            return None, rawmessage

        try:
            return _parse(rawmessage)
        except ParseError:
            logger.error(
                "Could not parse the message %s. Truncating invalid data.",
                binascii.hexlify(rawmessage),
            )
            rawmessage = _trim_buffer_garbage(
                rawmessage[1:]
            )  # try to find possible start of a message


class ParseError(Exception):
    """Exception raised for errors in the parsing of raw messages."""


def _parse(rawmessage: bytearray) -> tuple[RawMessage | None, bytearray]:
    """Parse a RawMessage from a bytearray buffer."""
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
        logger.debug(
            "Trimming whole buffer as it does not contain the start byte: %s",
            binascii.hexlify(rawmessage),
        )
        return []

    return rawmessage
