"""The velbus abstract message class."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import enum
import json
import struct
from typing import Any

from velbusaio.const import PRIORITY_FIRMWARE, PRIORITY_HIGH, PRIORITY_LOW


class ParserError(Exception):
    """Error when invalid message is received."""


@dataclass
class FieldSpec:
    """Specification for a message field.

    Attributes:
        name: Field name for attribute assignment
        fmt: Struct format character (e.g., 'B' for unsigned byte, 'H' for unsigned short)
        decode: Optional function to transform value after unpacking (value -> decoded_value)
        encode: Optional function to transform value before packing (value -> encoded_value)
        validate: Optional function to validate value (raises exception if invalid)
    """

    name: str
    fmt: str
    decode: Callable[[Any], Any] | None = None
    encode: Callable[[Any], Any] | None = None
    validate: Callable[[Any], None] | None = None


class Message:
    """Base Velbus message."""

    # Class-level declarative schema hooks
    command_code: int | None = None  # Command code for this message type
    fields: list[FieldSpec] | None = (
        None  # Field specifications for declarative parsing
    )
    validators: list[Callable[[Message], None]] | None = (
        None  # Message-level validators
    )
    byte_order: str = ">"  # Struct byte order (default: big-endian)
    default_priority: int = PRIORITY_LOW  # Default priority for this message type
    default_rtr: bool = False  # Default RTR flag for this message type

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

    def populate(self, priority: int, address: int, rtr: bool, data: bytes) -> None:
        """Populate message from raw data.

        Generic implementation that uses the declarative field schema.
        Subclasses should either define fields or override this method.
        """
        # Check if subclass uses declarative schema
        if self.fields is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'fields' or override populate()"
            )

        # Set basic attributes
        self.set_attributes(priority, address, rtr)

        # Run validators if defined
        if self.validators:
            for validator in self.validators:
                validator(self)

        # Build struct format from fields
        fmt = self.byte_order + "".join(field.fmt for field in self.fields)
        expected_length = struct.calcsize(fmt)

        # Validate data length
        if len(data) < expected_length:
            self.parser_error(
                f"needs {expected_length} bytes of data, have {len(data)}"
            )

        # Unpack data according to field specifications
        values = struct.unpack(fmt, data[:expected_length])

        # Apply decode and validation per field, then assign attributes
        for field, value in zip(self.fields, values, strict=True):
            # Apply decode transformation if specified
            if field.decode:
                value = field.decode(value)

            # Apply field-level validation if specified
            if field.validate:
                field.validate(value)

            # Assign to attribute
            setattr(self, field.name, value)

    def set_defaults(self, address: int | None) -> None:
        """Set defaults.

        If a message has different than low priority or NO_RTR set,
        then this method can be overridden in subclass, or use
        default_priority/default_rtr class attributes.
        """
        if address is not None:
            self.set_address(address)

        # Use class-level defaults if defined
        if self.default_priority == PRIORITY_LOW:
            self.set_low_priority()
        elif self.default_priority == PRIORITY_HIGH:
            self.set_high_priority()
        elif self.default_priority == PRIORITY_FIRMWARE:
            self.set_firmware_priority()
        else:
            self.priority = self.default_priority

        if self.default_rtr:
            self.set_rtr()
        else:
            self.set_no_rtr()

    def set_address(self, address: int) -> None:
        """Set the address of the message."""
        self.address = address

    def data_to_binary(self) -> bytes:
        """Convert message data to binary format.

        Generic implementation that uses the declarative field schema.
        Subclasses should either define fields/command_code or override this method.
        """
        # Check if subclass uses declarative schema
        if self.fields is None or self.command_code is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'fields' and 'command_code' "
                "or override data_to_binary()"
            )

        # Prepare values for packing
        values = []
        for field in self.fields:
            value = getattr(self, field.name)

            # Apply field-level validation if specified
            if field.validate:
                field.validate(value)

            # Apply encode transformation if specified
            if field.encode:
                value = field.encode(value)

            values.append(value)

        # Build struct format and pack
        fmt = self.byte_order + "".join(field.fmt for field in self.fields)
        packed_data = struct.pack(fmt, *values)

        # Prefix with command code
        return bytes([self.command_code]) + packed_data

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
        if not data:
            return
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
