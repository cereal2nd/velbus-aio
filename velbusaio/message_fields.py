"""Field descriptors for declarative Velbus message definitions.

This module provides a declarative way to define message structures,
eliminating boilerplate in populate() and data_to_binary() methods.
"""

from __future__ import annotations

from collections.abc import Callable
import json
from typing import Any, ClassVar

from velbusaio.command_registry import CommandRegistryError, commandRegistry
from velbusaio.message import Message


class Field:
    """Base field descriptor for message attributes."""

    serializable: bool = True

    def __init__(
        self,
        byte_index: int | None = None,
        default: Any = None,
        parser: Callable[[bytes], Any] | None = None,
        serializer: Callable[[Any], bytes] | None = None,
        *,
        serializable: bool | None = None,
        json_map: dict[Any, Any] | None = None,
    ) -> None:
        """Initialize field descriptor."""
        self.byte_index = byte_index
        self.default = default
        self.parser = parser
        self.serializer = serializer
        self.json_map = json_map
        if serializable is not None:
            self.serializable = serializable
        self.name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Store the field name."""
        self.name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        """Get the field value."""
        if obj is None:
            return self
        if self.name is None:
            raise AttributeError("Field name is not set")
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        """Set the field value."""
        if self.name is None:
            raise AttributeError("Field name is not set")
        obj.__dict__[self.name] = value

    def parse(self, data: bytes) -> Any:
        """Parse value from data bytes."""
        if self.parser is not None:
            return self.parser(data)
        if self.byte_index is not None:
            return data[self.byte_index]
        return self.default

    def serialize(self, value: Any) -> bytes:
        """Serialize value to bytes."""
        if self.serializer is not None:
            return self.serializer(value)
        if isinstance(value, int):
            return bytes([value])
        return b""

    def to_json_value(self, value: Any) -> Any:
        """Convert a parsed value for JSON output."""
        if self.json_map is not None:
            return self.json_map.get(value, value)
        return value


class ByteField(Field):
    """Single byte field."""

    def __init__(self, byte_index: int, default: int | None = 0, **kwargs: Any) -> None:
        """Initialize byte field."""
        super().__init__(byte_index=byte_index, default=default, **kwargs)

    def parse(self, data: bytes) -> int:
        """Parse byte from data."""
        assert self.byte_index is not None
        return data[self.byte_index]

    def serialize(self, value: int) -> bytes:
        """Serialize to single byte."""
        return bytes([value])


class BitField(Field):
    """Bit or bit-mask field within a single byte."""

    def __init__(
        self,
        byte_index: int,
        mask: int,
        *,
        shift: int = 0,
        default: Any = 0,
        as_bool: bool = False,
        json_map: dict[Any, Any] | None = None,
        serializable: bool = False,
    ) -> None:
        """Initialize bit field."""
        super().__init__(
            byte_index=byte_index,
            default=default,
            json_map=json_map,
            serializable=serializable,
        )
        self.mask = mask
        self.shift = shift
        self.as_bool = as_bool

    def parse(self, data: bytes) -> Any:
        """Parse masked bits from data."""
        assert self.byte_index is not None
        value = data[self.byte_index] & self.mask
        if self.shift:
            value >>= self.shift
        if self.as_bool:
            return value != 0
        return value

    def serialize(self, value: Any) -> bytes:
        """Serialize bit field (rarely used on transmit messages)."""
        if self.as_bool:
            bit_value = self.mask if value else 0
        else:
            bit_value = (int(value) << self.shift) & self.mask
        return bytes([bit_value])


class MappedField(Field):
    """Field whose JSON representation uses a lookup map."""

    def __init__(
        self,
        byte_index: int | None = None,
        *,
        default: Any = None,
        parser: Callable[[bytes], Any] | None = None,
        serializer: Callable[[Any], bytes] | None = None,
        json_map: dict[Any, Any] | None = None,
        serializable: bool = True,
    ) -> None:
        """Initialize mapped field."""
        super().__init__(
            byte_index=byte_index,
            default=default,
            parser=parser,
            serializer=serializer,
            json_map=json_map,
            serializable=serializable,
        )


class ComputedField(Field):
    """Derived field populated from data but not tied to a fixed byte index."""

    def __init__(
        self,
        parser: Callable[[bytes], Any],
        *,
        default: Any = None,
        serializer: Callable[[Any], bytes] | None = None,
        serializable: bool = False,
        json_map: dict[Any, Any] | None = None,
    ) -> None:
        """Initialize computed field."""
        super().__init__(
            byte_index=None,
            default=default,
            parser=parser,
            serializer=serializer,
            serializable=serializable,
            json_map=json_map,
        )


class RawTailField(Field):
    """Remaining bytes from a start index."""

    def __init__(self, start_index: int, default: bytes = b"") -> None:
        """Initialize raw tail field."""
        super().__init__(
            byte_index=start_index,
            default=default,
            parser=lambda data, start=start_index: data[start:],
            serializer=bytes,
            serializable=True,
        )
        self.start_index = start_index

    def parse(self, data: bytes) -> bytes:
        """Parse remaining bytes."""
        return data[self.start_index :]


class ChannelsField(Field):
    """Field for channel bitmask parsing."""

    def __init__(
        self, byte_index: int, default: list[int] | None = None, **kwargs: Any
    ) -> None:
        """Initialize channels field."""
        super().__init__(byte_index=byte_index, default=default or [], **kwargs)

    def parse(self, data: bytes) -> list[int]:
        """Parse channels from bitmask byte."""
        assert self.byte_index is not None
        byte_value = data[self.byte_index]
        return [offset + 1 for offset in range(8) if byte_value & (1 << offset)]

    def serialize(self, channels: list[int]) -> bytes:
        """Serialize channels to bitmask byte."""
        result = 0
        for offset in range(8):
            if offset + 1 in channels:
                result += 1 << offset
        return bytes([result])


class ChannelField(Field):
    """Field for single channel parsing from a bitmask byte."""

    def __init__(self, byte_index: int, default: int = 0, **kwargs: Any) -> None:
        """Initialize channel field."""
        super().__init__(byte_index=byte_index, default=default, **kwargs)

    def parse(self, data: bytes) -> int:
        """Parse single channel from bitmask byte."""
        assert self.byte_index is not None
        byte_value = data[self.byte_index]
        channels = [offset + 1 for offset in range(8) if byte_value & (1 << offset)]
        if len(channels) != 1:
            raise ValueError(f"Expected exactly one channel, got {len(channels)}")
        return channels[0]

    def serialize(self, channel: int) -> bytes:
        """Serialize single channel to bitmask byte."""
        if channel <= 0:
            return bytes([0x00])
        return bytes([1 << (channel - 1)])


class ChannelIndexField(Field):
    """Channel index byte (1-8), stored as list[int] for API consistency."""

    def __init__(
        self, byte_index: int, default: list[int] | None = None, **kwargs: Any
    ) -> None:
        """Initialize channel index field."""
        super().__init__(byte_index=byte_index, default=default or [], **kwargs)

    def parse(self, data: bytes) -> list[int]:
        """Parse channel index byte to list of one channel (or empty)."""
        assert self.byte_index is not None
        value = data[self.byte_index]
        return [value] if value else []

    def serialize(self, channels: list[int]) -> bytes:
        """Serialize first channel to index byte (1-8), or 0 if empty."""
        return bytes([channels[0] if channels else 0])


class Int16Field(Field):
    """16-bit integer field (big-endian)."""

    def __init__(
        self,
        byte_index: int,
        default: int | None = 0,
        *,
        signed: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize 16-bit field."""
        super().__init__(byte_index=byte_index, default=default, **kwargs)
        self.signed = signed

    def parse(self, data: bytes) -> int:
        """Parse 16-bit value from two bytes."""
        assert self.byte_index is not None
        value = (data[self.byte_index] << 8) | data[self.byte_index + 1]
        if self.signed and value & 0x8000:
            value -= 0x10000
        return value

    def serialize(self, value: int) -> bytes:
        """Serialize to two bytes (big-endian)."""
        if value < 0:
            value += 0x10000
        return bytes([value >> 8, value & 0xFF])


class Int24Field(Field):
    """24-bit integer field (big-endian, 3 bytes)."""

    def __init__(self, byte_index: int, default: int = 0, **kwargs: Any) -> None:
        """Initialize 24-bit field."""
        super().__init__(byte_index=byte_index, default=default, **kwargs)

    def parse(self, data: bytes) -> int:
        """Parse 24-bit value from three bytes."""
        assert self.byte_index is not None
        return (
            (data[self.byte_index] << 16)
            | (data[self.byte_index + 1] << 8)
            | data[self.byte_index + 2]
        )

    def serialize(self, value: int) -> bytes:
        """Serialize to three bytes (big-endian)."""
        return bytes([value >> 16, (value >> 8) & 0xFF, value & 0xFF])


class Int32Field(Field):
    """32-bit integer field (big-endian, 4 bytes)."""

    def __init__(self, byte_index: int, default: int = 0, **kwargs: Any) -> None:
        """Initialize 32-bit field."""
        super().__init__(byte_index=byte_index, default=default, **kwargs)

    def parse(self, data: bytes) -> int:
        """Parse 32-bit value from four bytes."""
        assert self.byte_index is not None
        return (
            (data[self.byte_index] << 24)
            | (data[self.byte_index + 1] << 16)
            | (data[self.byte_index + 2] << 8)
            | data[self.byte_index + 3]
        )

    def serialize(self, value: int) -> bytes:
        """Serialize to four bytes (big-endian)."""
        return bytes(
            [
                (value >> 24) & 0xFF,
                (value >> 16) & 0xFF,
                (value >> 8) & 0xFF,
                value & 0xFF,
            ]
        )


class BlindChannelField(Field):
    """Channel field for VMB1BL/VMB2BL blind modules."""

    def __init__(self, byte_index: int, default: int = 0, **kwargs: Any) -> None:
        """Initialize blind channel field."""
        super().__init__(byte_index=byte_index, default=default, **kwargs)

    def parse(self, data: bytes) -> int:
        """Parse channel from VMB1BL/VMB2BL encoding."""
        assert self.byte_index is not None
        tmp = (data[self.byte_index] >> 1) & 0x03
        return 1 if tmp == 1 else 2

    def serialize(self, channel: int) -> bytes:
        """Serialize channel to VMB1BL/VMB2BL byte."""
        return bytes([0x03 if channel == 1 else 0x0C])


class BlindStatusField(Field):
    """Status field for VMB1BL/VMB2BL blind status."""

    def __init__(
        self,
        byte_index: int,
        channel_byte_index: int = 0,
        default: int = 0,
        **kwargs: Any,
    ) -> None:
        """Initialize blind status field."""
        super().__init__(
            byte_index=byte_index, default=default, serializable=False, **kwargs
        )
        self.channel_byte_index = channel_byte_index

    def parse(self, data: bytes) -> int:
        """Parse 2-bit status for this channel from status byte."""
        assert self.byte_index is not None
        tmp = (data[self.channel_byte_index] >> 1) & 0x03
        channel = 1 if tmp == 1 else 2
        return (data[self.byte_index] >> ((channel - 1) * 2)) & 0x03

    def serialize(self, value: int) -> bytes:
        """Serialize placeholder for receive-only messages."""
        return bytes([value])


class TemperatureField(Field):
    """Temperature field with special Velbus encoding."""

    def __init__(self, byte_index: int, default: float = 0.0, **kwargs: Any) -> None:
        """Initialize temperature field."""
        super().__init__(byte_index=byte_index, default=default, **kwargs)

    def parse(self, data: bytes) -> float:
        """Parse temperature from two bytes."""
        assert self.byte_index is not None
        raw = (data[self.byte_index] << 8) | data[self.byte_index + 1]
        if raw >> 15:
            return -127 + (raw / 32 * 0.0625)
        return (raw / 32) * 0.0625

    def serialize(self, value: float) -> bytes:
        """Serialize temperature to two bytes."""
        if value < 0:
            raw = int((value + 127) / 0.0625 * 32) | 0x8000
        else:
            raw = int(value / 0.0625 * 32)
        return bytes([raw >> 8, raw & 0xFF])


class StringField(Field):
    """String field for text data."""

    def __init__(
        self,
        start_index: int,
        length: int | None = None,
        default: str = "",
        **kwargs: Any,
    ) -> None:
        """Initialize string field."""
        super().__init__(byte_index=start_index, default=default, **kwargs)
        self.length = length

    def parse(self, data: bytes) -> str:
        """Parse string from bytes."""
        assert self.byte_index is not None
        if self.length is not None:
            end_index = self.byte_index + self.length
            string_bytes = data[self.byte_index : end_index]
        else:
            string_bytes = data[self.byte_index :]
        return "".join(chr(x) for x in string_bytes if x != 0)

    def serialize(self, value: str) -> bytes:
        """Serialize string to bytes."""
        encoded = value.encode("ascii", "ignore")
        if self.length is None:
            return encoded
        padded = encoded[: self.length]
        return padded + bytes(self.length - len(padded))


def _collect_fields(cls: type) -> dict[str, Field]:
    """Collect Field descriptors from the class MRO."""
    fields: dict[str, Field] = {}
    for base in reversed(cls.__mro__):
        if base is object:
            continue
        fields.update(
            {
                name: value
                for name, value in base.__dict__.items()
                if isinstance(value, Field)
            }
        )
    return fields


def _make_set_defaults(
    cls: type[DeclarativeMessage],
) -> Callable[[Any, int | None], None]:
    """Build set_defaults honoring declarative message config."""

    def set_defaults(self: DeclarativeMessage, address: int | None) -> None:
        if address is not None:
            self.set_address(address)
        priority = cls._priority
        if priority == "low":
            self.set_low_priority()
        elif priority == "high":
            self.set_high_priority()
        elif priority == "firmware":
            self.set_firmware_priority()
        if cls._rtr:
            self.set_rtr()
        else:
            self.set_no_rtr()

    return set_defaults


def _make_init(cls: type, fields: dict[str, Field]) -> Callable[..., None]:
    """Build __init__ that seeds field defaults."""

    def __init__(self: DeclarativeMessage, address: int | None = None) -> None:
        Message.__init__(self)
        for field_name, field in fields.items():
            setattr(self, field_name, field.default)
        self.set_defaults(address)

    return __init__


def _validate_populate(
    self: DeclarativeMessage, priority: int, rtr: bool, data: bytes
) -> None:
    """Run standard populate validations."""
    priority_setting = self._priority
    if priority_setting == "low":
        self.needs_low_priority(priority)
    elif priority_setting == "high":
        self.needs_high_priority(priority)
    elif priority_setting == "firmware":
        self.needs_firmware_priority(priority)

    if self._rtr:
        self.needs_rtr(rtr)
    else:
        self.needs_no_rtr(rtr)

    data_length = self._data_length
    if data_length is not None:
        if data_length == 0:
            self.needs_no_data(data)
        else:
            self.needs_data(data, data_length)


def _make_populate(cls: type, fields: dict[str, Field]) -> Callable[..., None]:
    """Build populate() from declared fields."""

    def populate(
        self: DeclarativeMessage,
        priority: int,
        address: int,
        rtr: bool,
        data: bytes,
    ) -> None:
        _validate_populate(self, priority, rtr, data)
        self.set_attributes(priority, address, rtr)
        for field_name, field in fields.items():
            setattr(self, field_name, field.parse(data))
        post_populate = getattr(self, "_post_populate", None)
        if post_populate is not None:
            post_populate(data)

    return populate


def _make_populate_no_fields(cls: type) -> Callable[..., None]:
    """Build populate() for messages with no declared fields."""

    def populate(
        self: DeclarativeMessage,
        priority: int,
        address: int,
        rtr: bool,
        data: bytes,
    ) -> None:
        _validate_populate(self, priority, rtr, data)
        self.set_attributes(priority, address, rtr)

    return populate


def _serializable_fields(fields: dict[str, Field]) -> list[tuple[str, Field]]:
    """Return fields included in data_to_binary in declaration order."""
    return [(name, field) for name, field in fields.items() if field.serializable]


def _make_data_to_binary_no_fields(
    cls: type[DeclarativeMessage],
) -> Callable[[Any], bytes]:
    """Build data_to_binary() for messages with no serializable fields."""

    def data_to_binary(self: DeclarativeMessage) -> bytes:
        return bytes([cls._command_code])

    return data_to_binary


def _make_data_to_binary(
    cls: type[DeclarativeMessage], fields: dict[str, Field]
) -> Callable[[Any], bytes]:
    """Build data_to_binary() from serializable fields."""

    serializable = _serializable_fields(fields)

    def data_to_binary(self: DeclarativeMessage) -> bytes:
        result = bytes([cls._command_code])
        for field_name, field in serializable:
            value = getattr(self, field_name, field.default)
            result += field.serialize(value)
        return result

    return data_to_binary


def _make_to_json_basic(
    cls: type, fields: dict[str, Field]
) -> Callable[[Any], dict[str, Any]]:
    """Build to_json_basic() including declared fields."""

    def to_json_basic(self: DeclarativeMessage) -> dict[str, Any]:
        payload = Message.to_json_basic(self)
        for field_name, field in fields.items():
            value = getattr(self, field_name, field.default)
            payload[field_name] = field.to_json_value(value)
        return payload

    return to_json_basic


def _make_to_json(cls: type, fields: dict[str, Field]) -> Callable[[Any], str]:
    """Build to_json() from to_json_basic()."""

    def to_json(self: DeclarativeMessage) -> str:
        return json.dumps(self.to_json_basic())

    return to_json


class DeclarativeMessage(Message):
    """Base class for declaratively defined Velbus messages."""

    _command_code: ClassVar[int]
    _module_types: ClassVar[list[str] | None] = None
    _priority: ClassVar[str | None] = "low"
    _rtr: ClassVar[bool] = False
    _data_length: ClassVar[int | None] = None
    _auto_register: ClassVar[bool] = False
    _generates_data_to_binary: ClassVar[bool] = True
    _generates_to_json: ClassVar[bool] = False

    _declarative_fields: ClassVar[dict[str, Field]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Configure generated methods and optional registry hooks."""
        super().__init_subclass__(**kwargs)

        fields = _collect_fields(cls)
        cls._declarative_fields = fields

        if cls._auto_register and hasattr(cls, "_command_code"):
            module_types = cls._module_types
            if not module_types:
                raise CommandRegistryError(
                    f"{cls.__name__} has _auto_register enabled but no _module_types"
                )
            for module_type in module_types:
                commandRegistry.register_command(cls._command_code, cls, module_type)

        if "__init__" not in cls.__dict__ and fields:
            cls.__init__ = _make_init(cls, fields)  # type: ignore[method-assign]

        if "set_defaults" not in cls.__dict__:
            cls.set_defaults = _make_set_defaults(cls)  # type: ignore[method-assign, assignment]

        if "populate" not in cls.__dict__:
            if fields:
                cls.populate = _make_populate(cls, fields)  # type: ignore[method-assign]
            else:
                cls.populate = _make_populate_no_fields(cls)  # type: ignore[method-assign]

        if (
            "data_to_binary" not in cls.__dict__
            and cls._generates_data_to_binary
            and hasattr(cls, "_command_code")
        ):
            if _serializable_fields(fields):
                cls.data_to_binary = _make_data_to_binary(cls, fields)  # type: ignore[method-assign, assignment]
            else:
                cls.data_to_binary = _make_data_to_binary_no_fields(cls)  # type: ignore[method-assign, assignment]

        if cls._generates_to_json:
            if "to_json_basic" not in cls.__dict__:
                cls.to_json_basic = _make_to_json_basic(cls, fields)  # type: ignore[method-assign, assignment]
            if "to_json" not in cls.__dict__:
                cls.to_json = _make_to_json(cls, fields)  # type: ignore[method-assign, assignment]
