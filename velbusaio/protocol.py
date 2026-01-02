"""Handles the Velbus protocol over asyncio transports."""

from __future__ import annotations

import asyncio
import binascii
import logging
import time
import typing as t
from asyncio import transports

import backoff

from velbusaio.const import MAXIMUM_MESSAGE_SIZE, MINIMUM_MESSAGE_SIZE, SLEEP_TIME
from velbusaio.raw_message import RawMessage
from velbusaio.raw_message import create as create_message_info


def _on_write_backoff(details):
    logging.debug(
        f"Transport is not open, waiting {details['wait']} seconds after {details['tries']}"
    )


class VelbusProtocol(asyncio.BufferedProtocol):
    """Handles the Velbus protocol.

    This class is expected to be wrapped inside a VelbusConnection class object which will maintain the socket
    and handle auto-reconnects
    """

    def __init__(
        self,
        message_received_callback: t.Callable[[RawMessage], t.Awaitable[None]],
        connection_state_callback: t.Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__()
        self._log = logging.getLogger("velbus-protocol")
        self._message_received_callback = message_received_callback
        self._connection_state_callback = connection_state_callback

        # everything for reading from Velbus
        self._buffer = bytearray(MAXIMUM_MESSAGE_SIZE)
        self._buffer_view = memoryview(self._buffer)
        self._buffer_pos = 0

        self._serial_buf = b""
        self.transport = None

        # everything for writing to Velbus
        self._send_queue = asyncio.Queue()
        self._write_transport_lock = asyncio.Lock()
        self._writer_task = None
        self._restart_writer = False
        self.restart_writing()

        self._closing = False
        self._background_tasks = set()

    def _notify_connection_state_callbacks(self, is_connected: bool) -> None:
        """Notify all registered callbacks of connection state change."""
        task = asyncio.ensure_future(self._connection_state_callback(is_connected))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def connection_made(self, transport: transports.BaseTransport) -> None:
        """Called when the Velbus connection is established."""
        self.transport = transport
        self._log.info("Connection established to Velbus")
        self._last_activity_time = time.time()

        self._restart_writer = True
        self.restart_writing()

        # Notify callbacks that connection is established
        self._notify_connection_state_callbacks(True)

    async def pause_writing(self) -> None:
        """Pause writing."""
        self._restart_writer = False
        if self._writer_task:
            self._send_queue.put_nowait(None)
        await asyncio.sleep(0.1)

    def restart_writing(self) -> None:
        """Resume writing."""
        if self._restart_writer and not self._write_transport_lock.locked():
            self._writer_task = asyncio.ensure_future(
                self._get_message_from_send_queue()
            )
            self._writer_task.add_done_callback(lambda _future: self.restart_writing())

    def close(self) -> None:
        """Close the Velbus connection."""
        self._closing = True
        self._restart_writer = False
        if self.transport:
            self.transport.close()

    def connection_lost(self, exc: t.Optional[Exception]) -> None:
        """Called when the Velbus connection is lost."""
        self.transport = None

        if self._closing:
            return  # Connection loss was expected, nothing to do here...
        if exc is None:
            self._log.warning("EOF received from Velbus")
        else:
            self._log.error(f"Velbus connection lost: {exc!r}")

        self.transport = None
        asyncio.ensure_future(self.pause_writing())

        # Notify callbacks that connection is lost
        self._notify_connection_state_callbacks(False)

    # Everything read-related

    def get_buffer(self, sizehint: int) -> memoryview:
        """Provide buffer for Buffered Streaming protocol."""
        return self._buffer_view[self._buffer_pos :]

    def data_received(self, data: bytes) -> None:
        """Receive data from the Streaming protocol.

        Called when asyncio.Protocol detects received data from serial port.
        """
        self._last_activity_time = time.time()
        self._serial_buf += data
        self._log.debug(
            "Received {nbytes} bytes from Velbus: {data_hex}".format(
                nbytes=len(data),
                data_hex=binascii.hexlify(self._serial_buf[: len(data)], " "),
            )
        )
        _recheck = True

        while len(self._serial_buf) > MINIMUM_MESSAGE_SIZE and _recheck:
            # try to construct a Velbus message from the buffer

            _remaining_buf = self._serial_buf[MAXIMUM_MESSAGE_SIZE:]
            msg, remaining_data = create_message_info(
                bytearray(self._serial_buf[:MAXIMUM_MESSAGE_SIZE])
            )

            if msg is not None:
                asyncio.ensure_future(self._process_message(msg))
                _recheck = True
            else:
                _recheck = False
            self._serial_buf = bytes(remaining_data) + _remaining_buf

    def buffer_updated(self, nbytes: int) -> None:
        """Receive data from the Buffered Streaming protocol.

        Called when asyncio.BufferedProtocol detects received data from network.
        """
        self._last_activity_time = time.time()
        self._buffer_pos += nbytes
        if self._buffer_pos > MINIMUM_MESSAGE_SIZE:
            # try to construct a Velbus message from the buffer
            msg, remaining_data = create_message_info(self._buffer)

            if msg is not None:
                asyncio.ensure_future(self._process_message(msg))

            self._new_buffer(remaining_data)

    def _new_buffer(self, remaining_data=None) -> None:
        new_buffer = bytearray(MAXIMUM_MESSAGE_SIZE)
        if remaining_data:
            new_buffer[: len(remaining_data)] = remaining_data

        self._buffer = new_buffer
        self._buffer_pos = len(remaining_data) if remaining_data else 0
        self._buffer_view = memoryview(self._buffer)

    async def _process_message(self, msg: RawMessage) -> None:
        # self._log.debug(f"RX: {msg}")
        await self._message_received_callback(msg)

    # Everything write-related

    async def write_auth_key(self, authkey: str) -> None:
        """Send authentication key to Velbus interface."""
        self._log.debug("TX: authentication key")
        if not self.transport.is_closing():
            self.transport.write(authkey.encode("utf-8"))

    async def send_message(self, msg: RawMessage) -> None:
        """Queue a message to be sent to Velbus."""
        self._send_queue.put_nowait(msg)

    async def _get_message_from_send_queue(self) -> None:
        """Get messages from the send queue and write them to Velbus."""
        self._log.debug("Starting Velbus write message from send queue")
        self._log.debug("Acquiring write lock")
        await self._write_transport_lock.acquire()
        while self._restart_writer:
            # wait for an item from the queue
            msg_info: RawMessage | None = await self._send_queue.get()
            if msg_info is None:
                self._restart_writer = False
                return
            message_sent = False
            try:
                start_time = time.perf_counter()
                while not message_sent:
                    message_sent = await self._write_message(msg_info)
                send_time = time.perf_counter() - start_time

                self._send_queue.task_done()  # indicate that the item of the queue has been processed

                queue_sleep_time = self._calculate_queue_sleep_time(msg_info, send_time)
                await asyncio.sleep(queue_sleep_time)

            except (asyncio.CancelledError, GeneratorExit) as exc:
                if not self._closing:
                    self._log.error(f"Stopping Velbus writer due to {exc!r}")
                self._restart_writer = False
            except Exception as exc:
                self._log.error(f"Restarting Velbus writer due to {exc!r}")
                self._restart_writer = True
        if self._write_transport_lock.locked():
            self._write_transport_lock.release()
        self._log.debug("Ending Velbus write message from send queue")

    @staticmethod
    def _calculate_queue_sleep_time(msg_info, send_time):
        """Calculate the sleep time needed after sending a message to Velbus."""
        sleep_time = SLEEP_TIME

        if msg_info.rtr:
            sleep_time = SLEEP_TIME  # this is a scan command. We could be quicker?

        if msg_info.command == 0xEF:
            # 'channel name request' command provokes in worst case 99 answer packets from VMBGPOD
            sleep_time = SLEEP_TIME * 33  # TODO make this adaptable on module_type

        if send_time > sleep_time:
            return 0  # no need to wait, we are already late
        return sleep_time - send_time

    @backoff.on_predicate(
        backoff.expo,
        lambda is_sent: not is_sent,
        max_tries=10,
        on_backoff=_on_write_backoff,
    )
    async def _write_message(self, msg: RawMessage) -> bool:
        """Write a message to Velbus."""
        self._log.debug(f"TX: {msg}")
        if not self.transport.is_closing():
            self.transport.write(msg.to_bytes())
            self._last_activity_time = time.time()
            return True
        return False

    async def wait_on_all_messages_sent_async(self) -> None:
        """Wait until all messages in the send queue are sent."""
        self._log.debug("Waiting on all messages sent")
        await self._send_queue.join()
