"""The velbus abstract message class."""

from __future__ import annotations

import enum
import json

from velbusaio.const import PRIORITY_FIRMWARE, PRIORITY_HIGH, PRIORITY_LOW


class ParserError(Exception):
    """Error when invalid message is received."""


class Message:
    """Base Velbus message."""

    def __init__(self, address: int = 0) -> None:
        """Initialize message with default values."""
        self.priority = PRIORITY_LOW
        self.address: int = 0
        self.rtr: bool = False
        self.data = bytearray()
        self.set_defaults(address)

    def set_attributes(self, priority: int, address: int, rtr: bool) -> None:
        """Set attributes of the message."""
        self.priority = priority
        self.address = address
        self.rtr = rtr

    def populate(self, priority: int, address: int, rtr: bool, data: int) -> None:
        """Populate message from raw data."""
        raise NotImplementedError

    def set_defaults(self, address: int | None) -> None:
        """Set defaults.

        If a message has different than low priority or NO_RTR set,
        then this method needs override in subclass
        """
        if address is not None:
            self.set_address(address)
        self.set_low_priority()
        self.set_no_rtr()

    def set_address(self, address: int) -> None:
        """Set the address of the message."""
        self.address = address

    def data_to_binary(self) -> bytes:
        """Convert message data to binary format."""
        raise NotImplementedError

    def to_json_basic(self) -> dict:
        """Create JSON structure with generic attributes."""
        me = {}
        me["name"] = str(self.__class__.__name__)
        me.update(self.__dict__.copy())
        for key in me.copy():
            if key == "name":
                continue
            if callable(getattr(self, key)) or key.startswith("__"):
                del me[key]
            if isinstance(me[key], (bytes, bytearray, enum.Enum)):
                me[key] = str(me[key])
            else:
                try:
                    json.dumps(me[key])  # Test if the value is JSON serializable
                except (TypeError, ValueError):
                    me[key] = str(me[key])  # Convert non-serializable objects to string
        return me

    def to_json(self) -> str:
        """Dump object structure to JSON.

        This method should be overridden in subclasses to include more than just generic attributes
        """
        return json.dumps(self.to_json_basic())

    def __str__(self) -> str:
        """Return string representation of the message."""
        return self.to_json()

    def byte_to_channels(self, byte: int) -> list[int]:
        """Convert a byte to a list of channels."""
        # pylint: disable-msg=R0201
        return [offset + 1 for offset in range(8) if byte & (1 << offset)]

    def channels_to_byte(self, channels: list[int]) -> int:
        """Convert a list of channels to a byte."""
        # pylint: disable-msg=R0201
        result = 0
        for offset in range(8):
            if offset + 1 in channels:
                result = result + (1 << offset)
        return result

    def byte_to_channel(self, byte: int) -> int:
        """Convert a byte to a single channel."""
        channels = self.byte_to_channels(byte)
        self.needs_one_channel(channels)
        return channels[0]

    def parser_error(self, message: str) -> None:
        """Raise a parser error with message."""
        raise ParserError(self.__class__.__name__ + " " + message)

    def needs_rtr(self, rtr: bool) -> None:
        """Check if rtr is set."""
        if not rtr:
            self.parser_error("needs rtr set")

    def set_rtr(self) -> None:
        """Set rtr flag."""
        self.rtr = True

    def needs_no_rtr(self, rtr: bool) -> None:
        """Check if rtr is not set."""
        if rtr:
            self.parser_error("does not need rtr set")

    def set_no_rtr(self) -> None:
        """Unset rtr flag."""
        self.rtr = False

    def needs_low_priority(self, priority: int) -> None:
        """Check if low priority is set."""
        if priority != PRIORITY_LOW:
            self.parser_error("needs low priority set")

    def set_low_priority(self) -> None:
        """Set low priority."""
        self.priority = PRIORITY_LOW

    def needs_high_priority(self, priority: int) -> None:
        """Check if high priority is set."""
        if priority != PRIORITY_HIGH:
            self.parser_error("needs high priority set")

    def set_high_priority(self) -> None:
        """Set high priority."""
        self.priority = PRIORITY_HIGH

    def needs_firmware_priority(self, priority: int) -> None:
        """Check if firmware priority is set."""
        if priority != PRIORITY_FIRMWARE:
            self.parser_error("needs firmware priority set")

    def set_firmware_priority(self) -> None:
        """Set firmware priority."""
        self.priority = PRIORITY_FIRMWARE

    def needs_no_data(self, data: bytes) -> None:
        """Check if no data is included."""
        length = len(data)
        if length != 0:
            self.parser_error("has data included")

    def needs_data(self, data: bytes, length: int) -> None:
        """Check if data of specific length is included."""
        if len(data) < length:
            self.parser_error(
                "needs " + str(length) + " bytes of data have " + str(len(data))
            )

    def needs_fixed_byte(self, byte: int, value: int) -> None:
        """Check if specific byte has specific value."""
        if byte != value:
            self.parser_error("expects " + chr(value) + " in byte " + chr(byte))

    def needs_one_channel(self, channels: list[int]) -> None:
        """Check if exactly one channel is included."""
        if (
            len(channels) != 1
            or not isinstance(channels[0], int)
            or not channels[0] > 0
            or not channels[0] <= 8
        ):
            self.parser_error("needs exactly one bit set in channel byte")
