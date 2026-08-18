"""Handles the Velbus protocol over asyncio transports."""

from __future__ import annotations

import asyncio
from asyncio import transports
import binascii
import logging
import time
import typing as t

from velbusaio.const import MAXIMUM_MESSAGE_SIZE, MINIMUM_MESSAGE_SIZE
from velbusaio.message import ParserError
from velbusaio.raw_message import RawMessage, create as create_message_info


class VelbusProtocol(asyncio.BufferedProtocol):
    """Handles the Velbus protocol framing and transport I/O."""

    def __init__(
        self,
        message_received_callback: t.Callable[[RawMessage], t.Awaitable[None]],
        on_disconnect_callback: t.Callable[[Exception | None], None] | None = None,
        auth_key: str | None = None,
    ) -> None:
        """Initialize VelbusProtocol with callbacks."""
        super().__init__()
        self._log = logging.getLogger("velbus-protocol")
        self._message_received_callback = message_received_callback
        self._on_disconnect_callback = on_disconnect_callback
        self._auth_key: str | None = auth_key

        # Everything for reading from Velbus

        # _buffer is a fixed scratch buffer the transport writes into on the
        # BufferedProtocol (get_buffer/buffer_updated) read path. buffer_updated()
        # copies the received bytes into _serial_buf, so both read paths converge
        # on the same framing logic in data_received().
        self._buffer = bytearray(MAXIMUM_MESSAGE_SIZE)
        self._buffer_view = memoryview(self._buffer)
        self._serial_buf = b""
        self.transport: asyncio.Transport | None = None
        self._last_activity_time: float = time.time()

        # Flow control
        self._can_write: asyncio.Event = asyncio.Event()
        self._closing = False

    @property
    def is_connected(self) -> bool:
        """Return whether transport is active and connected."""
        return self.transport is not None and not self.transport.is_closing()

    def pause_writing(self) -> None:
        """Called when transport output buffer exceeds high watermark."""
        self._can_write.clear()
        self._log.debug("Transport write paused (high watermark reached)")

    def resume_writing(self) -> None:
        """Called when transport output buffer drains below low watermark."""
        self._can_write.set()
        self._log.debug("Transport write resumed (low watermark reached)")

    async def wait_can_write(self) -> None:
        """Wait until transport is ready to accept writes."""
        await self._can_write.wait()

    def connection_made(self, transport: transports.BaseTransport) -> None:
        """Called when the Velbus connection is established."""
        self.transport = t.cast("asyncio.Transport", transport)
        self._can_write.set()
        self._log.info("Connection established to Velbus")

        if self._auth_key:
            self._log.debug("TX: authentication key")
            self.transport.write(self._auth_key.encode("utf-8"))

        self._last_activity_time = time.time()

    def close(self) -> None:
        """Close the Velbus connection."""
        self._closing = True

        # By setting _can_write here, we prevent deadlocks in the controller.
        self._can_write.set()
        if self.transport:
            self.transport.close()

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the Velbus connection is lost."""
        self.transport = None
        self._can_write.set()

        if self._closing:
            return  # Connection loss was expected, nothing to do here...
        if exc is None:
            self._log.warning("EOF received from Velbus")
        else:
            self._log.error(f"Velbus connection lost: {exc!r}")

        if self._on_disconnect_callback is not None:
            self._on_disconnect_callback(exc)

    # Read Path

    def get_buffer(self, sizehint: int) -> memoryview:
        """Provide a writable buffer for the BufferedProtocol read path.

        Returns the whole scratch buffer; the received bytes are copied out and
        accumulated in data_received(), so the transport may reuse it freely on
        the next read.
        """
        return self._buffer_view

    def data_received(self, data: bytes) -> None:
        """Receive data from the Streaming protocol.

        Called when asyncio.Protocol detects received data from serial port.
        """
        self._last_activity_time = time.time()
        self._serial_buf += data
        self._log.debug(
            "RX: {nbytes} bytes: {data_hex}".format(
                nbytes=len(data),
                data_hex=binascii.hexlify(self._serial_buf[: len(data)], " "),
            )
        )
        _recheck = True

        while len(self._serial_buf) >= MINIMUM_MESSAGE_SIZE and _recheck:
            # create_message_info() / _parse() reject buffers larger than one
            # maximum-size packet, so only feed it the first MAXIMUM_MESSAGE_SIZE
            # bytes. The bytes beyond that (a second packet that arrived in the
            # same read) must be preserved as the tail, otherwise they are
            # silently dropped on a busy bus where reads bundle multiple packets.
            head = bytearray(self._serial_buf[:MAXIMUM_MESSAGE_SIZE])
            tail = self._serial_buf[MAXIMUM_MESSAGE_SIZE:]

            msg, remaining_data = create_message_info(head)

            if msg is not None:
                asyncio.ensure_future(self._process_message(msg))  # noqa: RUF006
                _recheck = True
            else:
                _recheck = False
            self._serial_buf = bytes(remaining_data) + tail

    def buffer_updated(self, nbytes: int) -> None:
        """Receive data from the BufferedProtocol read path.

        Called when asyncio.BufferedProtocol detects received data. This path is
        used by the network transport and by serialx for serial ports. Delegate
        to data_received() so both read paths converge on the same robust framing
        logic. The previous implementation parsed a fixed-size buffer in place and
        swapped it mid-stream, which misframed the byte stream depending on how the
        transport chunked its reads (intact payloads but corrupt STX/ETX bytes).
        """
        self.data_received(bytes(self._buffer_view[:nbytes]))

    async def _process_message(self, msg: RawMessage) -> None:
        # self._log.debug(f"RX: {msg}")
        # This coroutine is scheduled as a detached task (asyncio.ensure_future),
        # so any exception it raises would otherwise surface as an unretrieved
        # "Task exception was never retrieved" error and kill the task silently.
        # A single malformed/short packet from a module must never take down the
        # processing pipeline, so swallow parse errors here and log a warning.
        try:
            await self._message_received_callback(msg)
        except ParserError as exc:
            self._log.warning(f"Dropping unparsable message ({exc}): {msg}")

    # Write Path

    def write_message(self, msg: RawMessage) -> bool:
        """Write a raw message to the Velbus transport."""
        self._log.debug(f"TX: {msg}")
        if self.transport and not self.transport.is_closing():
            self.transport.write(msg.to_bytes())
            self._last_activity_time = time.time()
            return True
        return False
