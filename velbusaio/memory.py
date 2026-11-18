"""Paced memory read/write helper for Velbus modules.

Handles EEPROM access with acknowledgement waiting so callers can safely
program action tables and other persistent settings.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
import struct
from typing import Final

from velbusaio.const import PRIORITY_LOW, SLEEP_TIME
from velbusaio.exceptions import VelbusMemoryTimeout, VelbusMemoryWriteBlocked
from velbusaio.message import Message
from velbusaio.messages.memory_data import MemoryDataMessage
from velbusaio.messages.memory_data_block import MemoryDataBlockMessage
from velbusaio.messages.read_data_block_from_memory import (
    ReadDataBlockFromMemoryMessage,
)
from velbusaio.messages.read_data_from_memory import ReadDataFromMemoryMessage
from velbusaio.messages.write_data_to_memory import WriteDataToMemoryMessage
from velbusaio.messages.write_memory_block import WriteMemoryBlockMessage

# Protocol remarks: wait for memory-data-block feedback after 0xCA writes;
# keep a small gap between single-byte 0xFC writes.
_WRITE_BYTE_GAP: Final = max(SLEEP_TIME, 0.02)
_DEFAULT_TIMEOUT: Final = 2.0
_BLOCK_SIZE: Final = 4


def split_address(address: int) -> tuple[int, int]:
    """Split a 16-bit memory address into high/low bytes."""
    high, low = struct.unpack(">BB", struct.pack(">H", address & 0xFFFF))
    return high, low


def join_address(high: int, low: int) -> int:
    """Join high/low address bytes into a 16-bit address."""
    return ((high & 0xFF) << 8) | (low & 0xFF)


class MemoryBackend:
    """Read/write Velbus module memory with pacing and ACK waiting."""

    def __init__(
        self,
        module_address: int,
        writer: Callable[[Message], Awaitable[None]],
        logger: logging.Logger | None = None,
        *,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the memory backend."""
        self._module_address = module_address
        self._writer = writer
        self._log = logger or logging.getLogger("velbus-memory")
        self._timeout = timeout
        self._cache: dict[int, int] = {}
        self._waiters: dict[int, asyncio.Future[bytes]] = {}
        self._lock = asyncio.Lock()
        self._write_blocked_reason: str | None = None

    def block_writes(self, reason: str) -> None:
        """Refuse every further write, because they would corrupt memory."""
        self._write_blocked_reason = reason

    @property
    def writes_blocked(self) -> bool:
        """Whether writing to this module's memory is refused."""
        return self._write_blocked_reason is not None

    def _assert_writable(self) -> None:
        if self._write_blocked_reason is not None:
            raise VelbusMemoryWriteBlocked(self._write_blocked_reason)

    @property
    def cache(self) -> dict[int, int]:
        """Return a copy of the known memory cache."""
        return dict(self._cache)

    def invalidate(self, start: int | None = None, end: int | None = None) -> None:
        """Drop cached bytes, optionally limited to an inclusive range."""
        if start is None:
            self._cache.clear()
            return
        end = start if end is None else end
        for addr in range(start, end + 1):
            self._cache.pop(addr, None)

    def feed_byte(self, address: int, data: int) -> None:
        """Store a single memory byte from a bus reply and wake waiters."""
        self._cache[address] = data & 0xFF
        self._resolve_waiter(address, bytes([data & 0xFF]))

    def feed_block(self, address: int, data: bytes) -> None:
        """Store a memory block from a bus reply and wake waiters."""
        for offset, value in enumerate(data):
            self._cache[address + offset] = value & 0xFF
        self._resolve_waiter(address, bytes(data))

    def feed_message(self, message: Message) -> None:
        """Feed a memory response message into the cache/waiters."""
        if isinstance(message, MemoryDataMessage):
            addr = join_address(message.high_address, message.low_address)
            self.feed_byte(addr, message.data)
        elif isinstance(message, MemoryDataBlockMessage):
            addr = join_address(message.high_address, message.low_address)
            self.feed_block(addr, bytes(message.data))

    def get_cached(self, address: int) -> int | None:
        """Return a cached byte, or None if unknown."""
        return self._cache.get(address)

    def get_cached_range(self, start: int, length: int) -> bytes | None:
        """Return cached bytes for a range, or None if any byte is missing."""
        out = bytearray()
        for addr in range(start, start + length):
            if addr not in self._cache:
                return None
            out.append(self._cache[addr])
        return bytes(out)

    def seed_from_vlp_hex(self, memory_hex: str) -> None:
        """Seed the byte cache from a VLP EEPROM hex dump."""
        memory_hex = memory_hex.strip()
        if not memory_hex:
            return
        if len(memory_hex) % 2:
            raise ValueError("VLP memory hex must have an even number of characters")
        for addr in range(len(memory_hex) // 2):
            self._cache[addr] = int(memory_hex[addr * 2 : addr * 2 + 2], 16)

    async def read_byte(self, address: int, *, use_cache: bool = True) -> int:
        """Read one memory byte."""
        if use_cache and address in self._cache:
            return self._cache[address]
        async with self._lock:
            if use_cache and address in self._cache:
                return self._cache[address]
            high, low = split_address(address)
            msg = ReadDataFromMemoryMessage(self._module_address)
            msg.priority = PRIORITY_LOW
            msg.high_address = high
            msg.low_address = low
            data = await self._request(address, msg, expect_len=1)
            return data[0]

    async def read_bytes(
        self,
        start: int,
        length: int,
        *,
        use_cache: bool = True,
    ) -> bytes:
        """Read a contiguous memory range, preferring 4-byte blocks."""
        if length <= 0:
            return b""
        cached = self.get_cached_range(start, length) if use_cache else None
        if cached is not None:
            return cached
        async with self._lock:
            if use_cache:
                cached = self.get_cached_range(start, length)
                if cached is not None:
                    return cached
            return await self._read_range_unlocked(start, length, use_cache=use_cache)

    async def _read_range_unlocked(
        self, start: int, length: int, *, use_cache: bool = True
    ) -> bytes:
        out = bytearray()
        current = start
        end = start + length
        while current < end:
            remaining = end - current
            if remaining >= _BLOCK_SIZE:
                chunk_len = _BLOCK_SIZE
                if use_cache:
                    cached = self.get_cached_range(current, chunk_len)
                    if cached is not None:
                        out.extend(cached)
                        current += chunk_len
                        continue
                block = await self._read_block_unlocked(current)
                take = min(_BLOCK_SIZE, remaining)
                out.extend(block[:take])
                current += take
            else:
                if use_cache and current in self._cache:
                    out.append(self._cache[current])
                    current += 1
                    continue
                value = await self._read_byte_unlocked(current)
                out.append(value)
                current += 1
        return bytes(out)

    async def write_byte(self, address: int, value: int) -> None:
        """Write one memory byte and wait for the 0xFE acknowledgement."""
        self._assert_writable()
        async with self._lock:
            await self._write_byte_unlocked(address, value & 0xFF)
            await asyncio.sleep(_WRITE_BYTE_GAP)

    async def write_bytes(self, start: int, data: bytes) -> None:
        """Write a contiguous memory range using 4-byte blocks when possible."""
        self._assert_writable()
        if not data:
            return
        async with self._lock:
            current = start
            offset = 0
            while offset < len(data):
                remaining = len(data) - offset
                if remaining >= _BLOCK_SIZE:
                    chunk = data[offset : offset + _BLOCK_SIZE]
                    await self._write_block_unlocked(current, chunk)
                    current += _BLOCK_SIZE
                    offset += _BLOCK_SIZE
                else:
                    await self._write_byte_unlocked(current, data[offset])
                    await asyncio.sleep(_WRITE_BYTE_GAP)
                    current += 1
                    offset += 1

    async def _read_byte_unlocked(self, address: int) -> int:
        high, low = split_address(address)
        msg = ReadDataFromMemoryMessage(self._module_address)
        msg.priority = PRIORITY_LOW
        msg.high_address = high
        msg.low_address = low
        data = await self._request(address, msg, expect_len=1)
        return data[0]

    async def _read_block_unlocked(self, address: int) -> bytes:
        high, low = split_address(address)
        msg = ReadDataBlockFromMemoryMessage(self._module_address)
        msg.priority = PRIORITY_LOW
        msg.high_address = high
        msg.low_address = low
        return await self._request(address, msg, expect_len=_BLOCK_SIZE)

    async def _write_byte_unlocked(self, address: int, value: int) -> None:
        high, low = split_address(address)
        msg = WriteDataToMemoryMessage(self._module_address)
        msg.priority = PRIORITY_LOW
        msg.high_address = high
        msg.low_address = low
        msg.data = value
        await self._request(address, msg, expect_len=1)

    async def _write_block_unlocked(self, address: int, data: bytes) -> None:
        if len(data) != _BLOCK_SIZE:
            raise ValueError(f"Memory block writes require {_BLOCK_SIZE} bytes")
        high, low = split_address(address)
        msg = WriteMemoryBlockMessage(self._module_address)
        msg.priority = PRIORITY_LOW
        msg.high_address = high
        msg.low_address = low
        msg.data = data
        await self._request(address, msg, expect_len=_BLOCK_SIZE)

    async def _request(
        self, address: int, message: Message, *, expect_len: int
    ) -> bytes:
        """Send a memory request and wait for the matching reply."""
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[bytes] = loop.create_future()
        # Replace any stale waiter for this address.
        old = self._waiters.pop(address, None)
        if old is not None and not old.done():
            old.cancel()
        self._waiters[address] = fut
        try:
            await self._writer(message)
            data = await asyncio.wait_for(fut, self._timeout)
        except TimeoutError as err:
            raise VelbusMemoryTimeout(address) from err
        finally:
            current = self._waiters.get(address)
            if current is fut:
                self._waiters.pop(address, None)

        if len(data) < expect_len:
            # Single-byte ACKs for block writes are unexpected; pad from cache.
            padded = bytearray(data)
            while len(padded) < expect_len:
                cached = self._cache.get(address + len(padded))
                if cached is None:
                    break
                padded.append(cached)
            data = bytes(padded)
        return data

    def _resolve_waiter(self, address: int, data: bytes) -> None:
        fut = self._waiters.get(address)
        if fut is not None and not fut.done():
            fut.set_result(data)
