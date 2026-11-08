"""Action-table helpers for Velbus modules.

Classic relays/dimmers use per-channel 6-byte slots:

  [source_module_address, source_bit, action_code, time1, time2, time3]

Classic blinds (VMB2BLE / VMB1BLS) use per-channel 5-byte slots:

  [source_module_address, source_bit, action_code, time1, time2]

-20 relays use a shared 7-byte table (param4 = subject channel):

  [addr, bit, action_byte, t1, t2, t3, subject_channel]

-20 dimmers/blinds use a shared 6-byte table (subject in param3):

  [addr, bit, action_byte, t1, t2, t3]

Input modules use a shared 5-byte linked-button table:

  [addr, bit, action, time/param1, channel_param]

where channel_param is either a bit mask (classic pushbuttons) or a
channel number (glass panels / -20 inputs). Unused slots are 0xFF.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import importlib.resources
import json
import logging
from typing import TYPE_CHECKING, Any, Final, Literal

from velbusaio.exceptions import VelbusConfigError

if TYPE_CHECKING:
    from velbusaio.memory import MemoryBackend

_EMPTY: Final = 0xFF
_SLOT_SIZE_CLASSIC: Final = 6
_SLOT_SIZE_V2: Final = 7
_LOGGER = logging.getLogger("velbus-actions")

_CATALOG_CACHE: dict[str, dict[str, Any]] = {}

Layout = Literal["per_channel", "shared"]
SubjectEncoding = Literal[
    "param4",
    "param3",
    "param3_low3",
    "param2",
    "param2_bitmask",
]
_RELEASE_BIT_ENCODINGS: Final = frozenset({"param4", "param3", "param3_low3"})


def channel_to_bit(channel: int) -> int:
    """Convert a 1-based channel number to a Velbus channel bit mask."""
    if channel < 1 or channel > 8:
        raise VelbusConfigError(f"Channel must be 1..8, got {channel}")
    return 1 << (channel - 1)


def bit_to_channel(bit: int) -> int | None:
    """Convert a single-bit channel mask to a 1-based channel number."""
    if bit in (0, _EMPTY):
        return None
    if bit.bit_count() != 1:
        return None
    return bit.bit_length()


def load_action_catalog(catalog_id: str) -> dict[str, Any]:
    """Load an action catalog JSON by id (cached)."""
    if catalog_id in _CATALOG_CACHE:
        return _CATALOG_CACHE[catalog_id]
    try:
        with importlib.resources.path(
            "velbusaio", f"action_catalogs/{catalog_id}.json"
        ) as path:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as err:
        raise VelbusConfigError(f"Unknown action catalog '{catalog_id}'") from err
    _CATALOG_CACHE[catalog_id] = data
    return data


def resolve_action_code(catalog_id: str, action: str | int) -> int:
    """Resolve an action key or int code to a numeric action code."""
    if isinstance(action, int):
        return action & 0xFF
    catalog = load_action_catalog(catalog_id)
    actions = catalog.get("actions", {})
    needle = action.strip().lower()
    if needle.isdigit() or (
        len(needle) <= 2 and all(c in "0123456789abcdef" for c in needle)
    ):
        try:
            code = (
                int(needle, 16) if any(c in "abcdef" for c in needle) else int(needle)
            )
            if f"{code:02X}" in actions:
                return code
        except ValueError:
            pass
    for code_hex, meta in actions.items():
        if (
            meta.get("key", "").lower() == needle
            or meta.get("label", "").lower() == needle
        ):
            return int(code_hex, 16)
    raise VelbusConfigError(f"Unknown action '{action}' in catalog '{catalog_id}'")


def action_label(catalog_id: str, code: int) -> str:
    """Return a human-readable label for an action code."""
    catalog = load_action_catalog(catalog_id)
    meta = catalog.get("actions", {}).get(f"{code:02X}")
    if meta:
        return str(meta.get("label", f"0x{code:02X}"))
    return f"0x{code:02X}"


@dataclass(slots=True)
class ActionSlot:
    """One programmed input→output action slot."""

    slot: int
    source_address: int
    source_bit: int
    action_code: int
    time1: int
    time2: int
    time3: int
    catalog_id: str = "relay_classic"
    time4: int = _EMPTY
    on_release: bool = False
    slot_size: int = _SLOT_SIZE_CLASSIC
    subject_encoding: SubjectEncoding | None = None
    release_bit: bool = False

    @property
    def _uses_release_bit(self) -> bool:
        return self.release_bit

    def matches_channel(self, channel: int) -> bool:
        """Return True when this slot targets the given subject channel."""
        encoding = self.subject_encoding
        if encoding is None:
            return True
        if encoding == "param2_bitmask":
            mask = self.time2
            if mask in (0, _EMPTY):
                return False
            try:
                return bool(mask & channel_to_bit(channel))
            except VelbusConfigError:
                return False
        return self.subject_channel == channel

    @property
    def empty(self) -> bool:
        """Return True when the slot is unused (all 0xFF or invalid source)."""
        values = [
            self.source_address,
            self.source_bit,
            self.action_code,
            self.time1,
            self.time2,
        ]
        if self.slot_size >= _SLOT_SIZE_CLASSIC:
            values.append(self.time3)
        if self.slot_size >= _SLOT_SIZE_V2:
            values.append(self.time4)
        if all(value == _EMPTY for value in values):
            return True
        # Uninitialized EEPROM can contain 0x00 bytes; invalid sources are not programmed.
        return self.source_address in (0, _EMPTY)

    @property
    def source_channel(self) -> int | None:
        """Best-effort 1-based source channel from the bit mask."""
        return bit_to_channel(self.source_bit)

    @property
    def subject_channel(self) -> int | None:
        """Subject channel for shared tables."""
        encoding = self.subject_encoding
        if encoding == "param4":
            if self.time4 in (0, _EMPTY):
                return None
            return self.time4
        if encoding == "param3":
            if self.time3 in (0, _EMPTY):
                return None
            return self.time3
        if encoding == "param3_low3":
            if self.time3 == _EMPTY:
                return None
            channel = self.time3 & 0x07
            return channel or None
        if encoding == "param2":
            if self.time2 in (0, _EMPTY):
                return None
            return self.time2
        if encoding == "param2_bitmask":
            return bit_to_channel(self.time2)
        return None

    @property
    def action_key(self) -> str | None:
        """Catalog key for the action, if known."""
        catalog = load_action_catalog(self.catalog_id)
        meta = catalog.get("actions", {}).get(f"{self.action_code:02X}")
        return None if meta is None else str(meta.get("key"))

    @property
    def action_label(self) -> str:
        """Human-readable action label."""
        return action_label(self.catalog_id, self.action_code)

    @property
    def wire_action_byte(self) -> int:
        """Action byte as stored in EEPROM."""
        if self._uses_release_bit:
            return (
                (0x80 if self.on_release else 0x00) | (self.action_code & 0x7F)
            ) & 0xFF
        return self.action_code & 0xFF

    def to_bytes(self) -> bytes:
        """Serialize the slot to EEPROM bytes."""
        if self.empty:
            return bytes([_EMPTY] * self.slot_size)
        data = [
            self.source_address & 0xFF,
            self.source_bit & 0xFF,
            self.wire_action_byte,
            self.time1 & 0xFF,
            self.time2 & 0xFF,
        ]
        if self.slot_size >= _SLOT_SIZE_CLASSIC:
            data.append(self.time3 & 0xFF)
        if self.slot_size >= _SLOT_SIZE_V2:
            data.append(self.time4 & 0xFF)
        return bytes(data)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        payload = {
            "slot": self.slot,
            "empty": self.empty,
            "source_address": None if self.empty else self.source_address,
            "source_bit": None if self.empty else self.source_bit,
            "source_channel": self.source_channel,
            "action_code": None if self.empty else self.action_code,
            "action_key": self.action_key,
            "action_label": None if self.empty else self.action_label,
            "time1": None if self.empty else self.time1,
            "time2": None if self.empty else self.time2,
        }
        if self.slot_size >= _SLOT_SIZE_CLASSIC:
            payload["time3"] = None if self.empty else self.time3
        if self.slot_size >= _SLOT_SIZE_V2:
            payload["time4"] = None if self.empty else self.time4
        if self.subject_encoding is not None:
            payload["subject_channel"] = self.subject_channel
            if self.release_bit:
                payload["on_release"] = None if self.empty else self.on_release
            if self.subject_encoding == "param2_bitmask" and not self.empty:
                payload["subject_mask"] = self.time2
        return payload

    @classmethod
    def empty_slot(
        cls,
        slot: int,
        catalog_id: str = "relay_classic",
        *,
        slot_size: int = _SLOT_SIZE_CLASSIC,
        subject_encoding: SubjectEncoding | None = None,
        release_bit: bool = False,
    ) -> ActionSlot:
        """Create an unused slot."""
        return cls(
            slot=slot,
            source_address=_EMPTY,
            source_bit=_EMPTY,
            action_code=_EMPTY,
            time1=_EMPTY,
            time2=_EMPTY,
            time3=_EMPTY,
            time4=_EMPTY,
            catalog_id=catalog_id,
            slot_size=slot_size,
            subject_encoding=subject_encoding,
            release_bit=release_bit,
        )

    @classmethod
    def from_bytes(
        cls,
        slot: int,
        data: bytes,
        catalog_id: str = "relay_classic",
        *,
        slot_size: int | None = None,
        subject_encoding: SubjectEncoding | None = None,
        release_bit: bool = False,
    ) -> ActionSlot:
        """Parse an EEPROM slot."""
        size = slot_size or len(data)
        if len(data) < size:
            raise VelbusConfigError(
                f"Action slot requires {size} bytes, got {len(data)}"
            )
        action_byte = data[2]
        if release_bit:
            on_release = bool(action_byte & 0x80)
            action_code = action_byte & 0x7F if action_byte != _EMPTY else _EMPTY
        else:
            on_release = False
            action_code = action_byte
        return cls(
            slot=slot,
            source_address=data[0],
            source_bit=data[1],
            action_code=action_code,
            time1=data[3],
            time2=data[4],
            time3=data[5] if size >= _SLOT_SIZE_CLASSIC else _EMPTY,
            time4=data[6] if size >= _SLOT_SIZE_V2 else _EMPTY,
            on_release=on_release,
            catalog_id=catalog_id,
            slot_size=size,
            subject_encoding=subject_encoding,
            release_bit=release_bit,
        )

    @classmethod
    def create(
        cls,
        slot: int,
        *,
        source_address: int,
        source_channel: int | None = None,
        source_bit: int | None = None,
        action: str | int,
        time1: int = _EMPTY,
        time2: int = _EMPTY,
        time3: int = _EMPTY,
        time4: int = _EMPTY,
        on_release: bool = False,
        subject_channel: int | None = None,
        catalog_id: str = "relay_classic",
        slot_size: int = _SLOT_SIZE_CLASSIC,
        subject_encoding: SubjectEncoding | None = None,
        release_bit: bool = False,
    ) -> ActionSlot:
        """Build a programmed slot from friendly arguments."""
        if source_bit is None:
            if source_channel is None:
                raise VelbusConfigError("Provide source_channel or source_bit")
            source_bit = channel_to_bit(source_channel)
        action_code = resolve_action_code(catalog_id, action)
        if subject_channel is not None:
            if subject_encoding == "param4":
                time4 = subject_channel
            elif subject_encoding == "param3":
                time3 = subject_channel
            elif subject_encoding == "param3_low3":
                time3 = (
                    (time3 & 0xF8) | (subject_channel & 0x07)
                    if time3 != _EMPTY
                    else (subject_channel & 0x07)
                )
            elif subject_encoding == "param2":
                time2 = subject_channel
            elif subject_encoding == "param2_bitmask":
                time2 = channel_to_bit(subject_channel)
            else:
                time4 = subject_channel
        return cls(
            slot=slot,
            source_address=source_address & 0xFF,
            source_bit=source_bit & 0xFF,
            action_code=action_code & 0x7F if release_bit else action_code,
            time1=time1 & 0xFF,
            time2=time2 & 0xFF,
            time3=time3 & 0xFF,
            time4=time4 & 0xFF,
            on_release=on_release,
            catalog_id=catalog_id,
            slot_size=slot_size,
            subject_encoding=subject_encoding,
            release_bit=release_bit,
        )


class _SharedSlotStore:
    """Shared EEPROM slot cache for -20 / input style modules."""

    def __init__(
        self,
        memory: MemoryBackend,
        *,
        bank: int,
        slot_count: int,
        slot_size: int,
        catalog_id: str,
        subject_encoding: SubjectEncoding,
        release_bit: bool,
        logger: logging.Logger,
    ) -> None:
        self.memory = memory
        self.bank = bank
        self.slot_count = slot_count
        self.slot_size = slot_size
        self.catalog_id = catalog_id
        self.subject_encoding = subject_encoding
        self.release_bit = release_bit
        self._log = logger
        self.slots: list[ActionSlot] | None = None

    def _decode_slots(self, raw: bytes) -> list[ActionSlot]:
        slots: list[ActionSlot] = []
        for slot in range(self.slot_count):
            offset = slot * self.slot_size
            slots.append(
                ActionSlot.from_bytes(
                    slot,
                    raw[offset : offset + self.slot_size],
                    self.catalog_id,
                    slot_size=self.slot_size,
                    subject_encoding=self.subject_encoding,
                    release_bit=self.release_bit,
                )
            )
        return slots

    def decode_from_cache(self) -> bool:
        """Decode slots from the shadow EEPROM cache without bus access."""
        if self.slots is not None:
            return True
        length = self.slot_count * self.slot_size
        raw = self.memory.get_cached_range(self.bank, length)
        if raw is None:
            return False
        self.slots = self._decode_slots(raw)
        return True

    async def load(
        self, *, force: bool = False, prefetch: bool = False
    ) -> list[ActionSlot]:
        if self.slots is not None and not force:
            return self.slots
        if not force and self.decode_from_cache():
            assert self.slots is not None
            return self.slots
        if force:
            length = self.slot_count * self.slot_size
            self.memory.invalidate(self.bank, self.bank + length - 1)
            self.slots = None
        length = self.slot_count * self.slot_size
        raw = await self.memory.read_bytes(
            self.bank, length, use_cache=not force, prefetch=prefetch
        )
        self.slots = self._decode_slots(raw)
        return self.slots

    def slot_address(self, slot: int) -> int:
        if slot < 0 or slot >= self.slot_count:
            raise VelbusConfigError(
                f"Slot {slot} out of range 0..{self.slot_count - 1}"
            )
        return self.bank + (slot * self.slot_size)

    async def write_slot(self, entry: ActionSlot) -> None:
        address = self.slot_address(entry.slot)
        await self.memory.write_bytes(address, entry.to_bytes())
        if self.slots is None:
            self.slots = [
                ActionSlot.empty_slot(
                    i,
                    self.catalog_id,
                    slot_size=self.slot_size,
                    subject_encoding=self.subject_encoding,
                    release_bit=self.release_bit,
                )
                for i in range(self.slot_count)
            ]
        self.slots[entry.slot] = entry
        self._log.debug(
            "Wrote shared action slot %s @ 0x%04X: %s",
            entry.slot,
            address,
            entry.to_dict(),
        )


class ActionTable:
    """Action table view for one output channel."""

    def __init__(
        self,
        memory: MemoryBackend,
        *,
        channel: int,
        bank: int,
        slot_count: int = 39,
        slot_size: int = _SLOT_SIZE_CLASSIC,
        catalog_id: str = "relay_classic",
        noc_address: int | None = None,
        layout: Layout = "per_channel",
        subject_encoding: SubjectEncoding | None = None,
        release_bit: bool = False,
        shared_store: _SharedSlotStore | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize an action table for one channel."""
        self._memory = memory
        self.channel = channel
        self.bank = bank
        self.slot_count = slot_count
        self.slot_size = slot_size
        self.catalog_id = catalog_id
        self.noc_address = noc_address
        self.layout = layout
        self.subject_encoding = subject_encoding
        self.release_bit = release_bit
        self._shared = shared_store
        self._log = logger or _LOGGER
        self._slots: list[ActionSlot] | None = None
        self._normal_closed: bool | None = None

    @property
    def loaded(self) -> bool:
        """Return True when slots have been read from the module."""
        if self._shared is not None:
            return self._shared.slots is not None
        return self._slots is not None

    @property
    def shared_store(self) -> _SharedSlotStore | None:
        """Return the shared slot store, if this table uses one."""
        return self._shared

    def clear_decoded_cache(self) -> None:
        """Drop decoded action-table state without clearing EEPROM bytes."""
        self._slots = None
        self._normal_closed = None

    def decode_from_cache(self) -> bool:
        """Decode this table from the shadow EEPROM cache without bus access."""
        if self.loaded:
            return True
        if self._shared is not None:
            if not self._shared.decode_from_cache():
                return False
        else:
            length = self.slot_count * self.slot_size
            raw = self._memory.get_cached_range(self.bank, length)
            if raw is None:
                return False
            slots: list[ActionSlot] = []
            for slot in range(self.slot_count):
                offset = slot * self.slot_size
                slots.append(
                    ActionSlot.from_bytes(
                        slot,
                        raw[offset : offset + self.slot_size],
                        self.catalog_id,
                        slot_size=self.slot_size,
                        subject_encoding=self.subject_encoding,
                        release_bit=self.release_bit,
                    )
                )
            self._slots = slots
        if self.noc_address is not None:
            cached = self._memory.get_cached(self.noc_address)
            if cached is not None:
                self._normal_closed = cached == 0x00
        return True

    def _slot_address(self, slot: int) -> int:
        if self._shared is not None:
            return self._shared.slot_address(slot)
        if slot < 0 or slot >= self.slot_count:
            raise VelbusConfigError(
                f"Slot {slot} out of range 0..{self.slot_count - 1}"
            )
        return self.bank + (slot * self.slot_size)

    async def load(
        self, *, force: bool = False, prefetch: bool = False
    ) -> list[ActionSlot]:
        """Read all slots from module memory."""
        if force:
            length = self.slot_count * self.slot_size
            self._memory.invalidate(self.bank, self.bank + length - 1)
            self._slots = None
        elif self.decode_from_cache():
            return self.get_slots(include_empty=True)
        if self._shared is not None:
            slots = await self._shared.load(force=force, prefetch=prefetch)
        elif self._slots is not None and not force:
            slots = self._slots
        else:
            length = self.slot_count * self.slot_size
            raw = await self._memory.read_bytes(
                self.bank, length, use_cache=not force, prefetch=prefetch
            )
            slots = []
            for slot in range(self.slot_count):
                offset = slot * self.slot_size
                slots.append(
                    ActionSlot.from_bytes(
                        slot,
                        raw[offset : offset + self.slot_size],
                        self.catalog_id,
                        slot_size=self.slot_size,
                        subject_encoding=self.subject_encoding,
                        release_bit=self.release_bit,
                    )
                )
            self._slots = slots

        if self.noc_address is not None and (force or self._normal_closed is None):
            value = await self._memory.read_byte(
                self.noc_address, use_cache=not force, prefetch=prefetch
            )
            self._normal_closed = value == 0x00

        return list(slots)

    def _all_slots(self) -> list[ActionSlot]:
        if self._shared is not None:
            if self._shared.slots is None:
                raise VelbusConfigError("Action table not loaded; call load() first")
            return self._shared.slots
        if self._slots is None:
            raise VelbusConfigError("Action table not loaded; call load() first")
        return self._slots

    def get_slots(self, *, include_empty: bool = False) -> list[ActionSlot]:
        """Return cached slots for this channel; raises if not loaded."""
        slots = self._all_slots()
        if self.layout == "shared":
            slots = [
                slot
                for slot in slots
                if slot.empty or slot.matches_channel(self.channel)
            ]
        if include_empty:
            return list(slots)
        return [slot for slot in slots if not slot.empty]

    async def get_actions(
        self, *, refresh: bool = False, include_empty: bool = False
    ) -> list[ActionSlot]:
        """Load if needed and return slots for this channel."""
        if refresh:
            await self.load(force=True)
        elif not self.loaded and not self.decode_from_cache():
            await self.load(force=False)
        return self.get_slots(include_empty=include_empty)

    async def load_noc(self, *, refresh: bool = False, prefetch: bool = False) -> None:
        """Load only the NO/NC contact byte for this channel."""
        if self.noc_address is None:
            return
        if self._normal_closed is not None and not refresh:
            return
        value = await self._memory.read_byte(
            self.noc_address, use_cache=not refresh, prefetch=prefetch
        )
        self._normal_closed = value == 0x00

    async def get_normal_closed(self, *, refresh: bool = False) -> bool | None:
        """Return True when the relay contact is programmed as NC."""
        if self.noc_address is None:
            return None
        if self._normal_closed is not None and not refresh:
            return self._normal_closed
        if not refresh:
            cached = self._memory.get_cached(self.noc_address)
            if cached is not None:
                self._normal_closed = cached == 0x00
                return self._normal_closed
        value = await self._memory.read_byte(self.noc_address, use_cache=not refresh)
        self._normal_closed = value == 0x00
        return self._normal_closed

    def find_free_slot(self) -> int:
        """Return the first unused slot index in the backing table."""
        for slot in self._all_slots():
            if slot.empty:
                return slot.slot
        raise VelbusConfigError("Action table is full")

    async def set_action(
        self,
        *,
        source_address: int,
        action: str | int,
        source_channel: int | None = None,
        source_bit: int | None = None,
        time1: int = _EMPTY,
        time2: int = _EMPTY,
        time3: int = _EMPTY,
        time4: int = _EMPTY,
        on_release: bool = False,
        slot: int | None = None,
    ) -> ActionSlot:
        """Program a slot (auto-picks a free slot when slot is None)."""
        await self.load()
        bit = (
            source_bit
            if source_bit is not None
            else channel_to_bit(source_channel or 1)
        )
        if slot is None:
            for existing in self.get_slots():
                if existing.source_address == (
                    source_address & 0xFF
                ) and existing.source_bit == (bit & 0xFF):
                    slot = existing.slot
                    break
            else:
                slot = self.find_free_slot()

        entry = ActionSlot.create(
            slot,
            source_address=source_address,
            source_channel=source_channel,
            source_bit=source_bit,
            action=action,
            time1=time1,
            time2=time2,
            time3=time3,
            time4=time4,
            on_release=on_release,
            subject_channel=self.channel if self.layout == "shared" else None,
            catalog_id=self.catalog_id,
            slot_size=self.slot_size,
            subject_encoding=self.subject_encoding,
            release_bit=self.release_bit,
        )
        await self._write_slot(entry)
        return entry

    async def clear_action(self, slot: int) -> ActionSlot:
        """Clear one slot back to 0xFF."""
        await self.load()
        entry = ActionSlot.empty_slot(
            slot,
            self.catalog_id,
            slot_size=self.slot_size,
            subject_encoding=self.subject_encoding,
            release_bit=self.release_bit,
        )
        await self._write_slot(entry)
        return entry

    async def clear_actions_for_source(
        self,
        source_address: int,
        *,
        source_channel: int | None = None,
        source_bit: int | None = None,
    ) -> list[ActionSlot]:
        """Clear all slots matching a source for this channel."""
        await self.load()
        bit = None
        if source_bit is not None:
            bit = source_bit & 0xFF
        elif source_channel is not None:
            bit = channel_to_bit(source_channel)

        cleared: list[ActionSlot] = []
        for entry in list(self.get_slots()):
            if entry.source_address != (source_address & 0xFF):
                continue
            if bit is not None and entry.source_bit != bit:
                continue
            cleared.append(await self.clear_action(entry.slot))
        return cleared

    async def set_normal_closed(self, normal_closed: bool) -> None:
        """Program NO (False) or NC (True) contact behaviour."""
        if self.noc_address is None:
            raise VelbusConfigError("This channel has no NO/NC memory address")
        await self._memory.write_byte(self.noc_address, 0x00 if normal_closed else 0xFF)
        self._normal_closed = normal_closed

    async def _write_slot(self, entry: ActionSlot) -> None:
        if self._shared is not None:
            await self._shared.write_slot(entry)
            return
        address = self._slot_address(entry.slot)
        await self._memory.write_bytes(address, entry.to_bytes())
        if self._slots is None:
            self._slots = [
                ActionSlot.empty_slot(
                    i,
                    self.catalog_id,
                    slot_size=self.slot_size,
                    subject_encoding=self.subject_encoding,
                    release_bit=self.release_bit,
                )
                for i in range(self.slot_count)
            ]
        self._slots[entry.slot] = entry
        self._log.debug(
            "Wrote action slot %s @ 0x%04X: %s",
            entry.slot,
            address,
            entry.to_dict(),
        )


def reserved_ranges(memory_spec: dict[str, Any] | None) -> list[tuple[int, int]]:
    """Return the EEPROM ranges an action table must never touch.

    The module name and the channel names live in the same address space as the
    action table. A spec that sizes its table for the wrong firmware build runs
    straight into them: reading returns name characters dressed up as actions,
    and writing corrupts the name.
    """
    ranges: list[tuple[int, int]] = []
    if not memory_spec:
        return ranges

    sources = [memory_spec.get("ModuleName")]
    sources.extend(
        value
        for value in (memory_spec.get("Channels") or {}).values()
        if isinstance(value, str)
    )
    for source in sources:
        for raw_part in (source or "").split(";"):
            part = raw_part.strip()
            if "-" not in part:
                continue
            low, _, high = part.partition("-")
            try:
                ranges.append((int(low, 16), int(high, 16)))
            except ValueError:
                continue
    return ranges


def _slots_before_reserved(
    bank: int, slot_count: int, slot_size: int, reserved: Sequence[tuple[int, int]]
) -> int:
    """Return how many slots fit between bank and the nearest reserved range."""
    limit = min(
        (low for low, _high in reserved if low > bank),
        default=None,
    )
    if limit is None:
        return slot_count
    return max(0, min(slot_count, (limit - bank) // slot_size))


def build_action_tables(
    memory: MemoryBackend,
    spec: dict[str, Any],
    logger: logging.Logger | None = None,
    *,
    reserved: Sequence[tuple[int, int]] | None = None,
) -> dict[int, ActionTable]:
    """Build per-channel ActionTable instances from a module_spec ActionTable block.

    `reserved` holds ranges the table must stay out of, as returned by
    reserved_ranges(). Slots that would fall inside one are dropped and a
    NO/NC address that lands in one is ignored, so a spec that disagrees with
    the module's firmware costs a few slots instead of the module name.
    """
    if not spec:
        return {}
    log = logger or _LOGGER
    layout: Layout = spec.get("layout", "per_channel")
    slot_count = int(spec.get("slot_count", 39))
    slot_size = int(spec.get("slot_size", _SLOT_SIZE_CLASSIC))
    catalog_id = str(spec.get("actions", "relay_classic"))
    subject_encoding: SubjectEncoding | None = spec.get("subject_encoding")
    if subject_encoding is None and layout == "shared":
        subject_encoding = "param4" if slot_size >= _SLOT_SIZE_V2 else "param3_low3"
    release_bit = spec.get("release_bit")
    if release_bit is None:
        release_bit = subject_encoding in _RELEASE_BIT_ENCODINGS
    else:
        release_bit = bool(release_bit)
    channels = spec.get("channels", {})
    tables: dict[int, ActionTable] = {}
    guard = list(reserved or ())

    shared_store: _SharedSlotStore | None = None
    shared_bank = 0
    shared_slot_count = slot_count
    if layout == "shared":
        if subject_encoding is None:
            raise VelbusConfigError("Shared action tables require subject_encoding")
        shared_bank = int(str(spec["bank"]), 16)
        shared_slot_count = _slots_before_reserved(
            shared_bank, slot_count, slot_size, guard
        )
        if shared_slot_count < slot_count:
            log.warning(
                "Action table at 0x%04X declares %d slots but only %d fit before "
                "reserved memory; ignoring the rest",
                shared_bank,
                slot_count,
                shared_slot_count,
            )
        shared_store = _SharedSlotStore(
            memory,
            bank=shared_bank,
            slot_count=shared_slot_count,
            slot_size=slot_size,
            catalog_id=catalog_id,
            subject_encoding=subject_encoding,
            release_bit=release_bit,
            logger=log,
        )

    for chan_key, chan_spec in channels.items():
        channel = int(chan_key)
        bank = shared_bank if layout == "shared" else int(str(chan_spec["bank"]), 16)
        if layout == "shared":
            channel_slot_count = shared_slot_count
        else:
            channel_slot_count = _slots_before_reserved(
                bank, slot_count, slot_size, guard
            )
            if channel_slot_count < slot_count:
                log.warning(
                    "Action table for channel %d at 0x%04X declares %d slots but "
                    "only %d fit before reserved memory; ignoring the rest",
                    channel,
                    bank,
                    slot_count,
                    channel_slot_count,
                )

        noc = chan_spec.get("noc_address")
        noc_address = int(str(noc), 16) if noc is not None else None
        if noc_address is not None and any(
            low <= noc_address <= high for low, high in guard
        ):
            log.warning(
                "NO/NC address 0x%04X for channel %d falls inside reserved memory; "
                "not reading or writing it",
                noc_address,
                channel,
            )
            noc_address = None

        tables[channel] = ActionTable(
            memory,
            channel=channel,
            bank=bank,
            slot_count=channel_slot_count,
            slot_size=slot_size,
            catalog_id=catalog_id,
            noc_address=noc_address,
            layout=layout,
            subject_encoding=subject_encoding,
            release_bit=release_bit,
            shared_store=shared_store,
            logger=log,
        )
    return tables


def iter_action_options(catalog_id: str = "relay_classic") -> Iterable[dict[str, Any]]:
    """Yield catalog action metadata for UI option lists."""
    catalog = load_action_catalog(catalog_id)
    for code_hex, meta in catalog.get("actions", {}).items():
        yield {
            "code": int(code_hex, 16),
            "code_hex": code_hex,
            "key": meta.get("key"),
            "label": meta.get("label"),
            "times": meta.get("times", 0),
            "time_labels": meta.get("time_labels", []),
        }
