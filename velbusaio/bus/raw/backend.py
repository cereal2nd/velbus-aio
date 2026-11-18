"""Direct Velbus protocol backend for :class:`~velbusaio.controller.Velbus`."""

from __future__ import annotations

import asyncio
import datetime
import logging
import re
import ssl
import time
import typing as t
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

import serialx

from velbusaio.bus.base import AuthFailedCallback
from velbusaio.const import SLEEP_TIME
from velbusaio.exceptions import VelbusConnectionFailed
from velbusaio.message import Message
from velbusaio.messages.set_date import SetDate
from velbusaio.messages.set_daylight_saving import SetDaylightSaving
from velbusaio.messages.set_realtime_clock import SetRealtimeClock
from velbusaio.protocol import VelbusProtocol
from velbusaio.raw_message import RawMessage
from velbusaio.vlp_reader import VlpFile, parse_vlp_sub_address_map

if TYPE_CHECKING:
    from velbusaio.controller import Velbus

_LOGGER = logging.getLogger(__name__)


class RawBusBackend:
    """Velbus controller backend over serial, TCP, or TLS."""

    def __init__(self, controller: Velbus, dsn: str) -> None:
        """Store transport DSN and outbound queue for the given controller."""
        self.controller = controller
        self._destination = dsn
        self._send_queue: asyncio.Queue[RawMessage] = asyncio.Queue()
        self._connected_event: asyncio.Event = asyncio.Event()
        self._protocol: VelbusProtocol | None = None
        self._send_task: asyncio.Task[None] | None = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Return whether the Velbus transport is up."""
        return self._is_connected

    @property
    def send_queue(self) -> asyncio.Queue[RawMessage]:
        """Outbound message queue (used by tests)."""
        return self._send_queue

    def add_auth_failed_callback(self, meth: AuthFailedCallback) -> None:
        """Raw bus transport does not use Signum Manager tokens."""

    def remove_auth_failed_callback(self, meth: AuthFailedCallback) -> None:
        """No-op for raw transport."""

    @staticmethod
    def calculate_queue_sleep_time(msg_info: RawMessage, send_time: float) -> float:
        """Calculate pacing delay after sending a message."""
        sleep_time = SLEEP_TIME
        if msg_info.rtr:
            sleep_time = SLEEP_TIME
        if msg_info.command == 0xEF:
            sleep_time = SLEEP_TIME * 33
        if send_time > sleep_time:
            return 0
        return sleep_time - send_time

    async def _send_loop(self) -> None:
        """Drain the send queue when the transport is connected."""
        _LOGGER.debug("Starting Velbus send loop")
        ctrl = self.controller
        while not ctrl.is_closing():
            try:
                await self._connected_event.wait()
                if ctrl.is_closing():
                    break
                msg_info: RawMessage = await self._send_queue.get()
                try:
                    message_sent = False
                    while not message_sent and not ctrl.is_closing():
                        await self._connected_event.wait()
                        if ctrl.is_closing():
                            break
                        if not (
                            self._is_connected
                            and self._protocol
                            and self._protocol.is_connected
                        ):
                            self._connected_event.clear()
                            await asyncio.sleep(0)
                            continue
                        await self._protocol.wait_can_write()
                        if ctrl.is_closing() or not (
                            self._is_connected
                            and self._protocol
                            and self._protocol.is_connected
                        ):
                            if not ctrl.is_closing():
                                self._connected_event.clear()
                            await asyncio.sleep(0)
                            continue
                        start_time = time.monotonic()
                        message_sent = self._protocol.write_message(msg_info)
                        if message_sent:
                            send_time = time.monotonic() - start_time
                            sleep_time = self.calculate_queue_sleep_time(
                                msg_info, send_time
                            )
                            if sleep_time > 0 and not ctrl.is_closing():
                                await asyncio.sleep(sleep_time)
                        elif not ctrl.is_closing():
                            self._connected_event.clear()
                            await asyncio.sleep(0)
                finally:
                    self._send_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                _LOGGER.exception("Error in Velbus send loop")
        _LOGGER.debug("Ending Velbus send loop")

    def _on_disconnect(self, exc: Exception | None) -> None:
        """Handle protocol disconnect from the transport thread."""
        self._is_connected = False
        self._connected_event.clear()
        task = asyncio.ensure_future(self.controller.notify_connection_state(False))
        self.controller.add_background_task(task)

    def _protocol_factory(self) -> VelbusProtocol:
        dest_parts = urlparse(self._destination)
        return VelbusProtocol(
            message_received_callback=self.controller.deliver_message,
            on_disconnect_callback=self._on_disconnect,
            auth_key=dest_parts.username or None,
        )

    async def connect(self) -> None:
        """Open serial or TCP/TLS transport."""
        ctrl = self.controller
        if self._send_task is None or self._send_task.done():
            self._send_task = asyncio.create_task(self._send_loop())
        destination = self._destination
        has_scheme = bool(re.search(r"^[A-Za-z0-9+.\-]+://", destination))
        is_bare_host_port = bool(re.search(r"^[^/]+:\d+$", destination))

        tcp_destination: str | None = None
        if has_scheme:
            parts = urlparse(destination)
            if parts.scheme in {"tcp", "tls"}:
                tcp_destination = destination
        elif is_bare_host_port:
            tcp_destination = f"tcp://{destination}"

        if tcp_destination is not None:
            parts = urlparse(tcp_destination)
            if parts.scheme == "tls":
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            else:
                ctx = None
            if parts.hostname is None or parts.port is None:
                raise VelbusConnectionFailed
            try:
                (
                    _transport,
                    tcp_protocol,
                ) = await asyncio.get_running_loop().create_connection(
                    self._protocol_factory,
                    host=parts.hostname,
                    port=parts.port,
                    ssl=ctx,
                )
                self._protocol = tcp_protocol
            except (ConnectionRefusedError, OSError) as err:
                raise VelbusConnectionFailed from err
            if ctrl.is_closing():
                if self._protocol:
                    self._protocol.close()
                return
            self._is_connected = True
            self._connected_event.set()
            await ctrl.notify_connection_state(True)
            return

        try:
            serial_factory = cast(
                "t.Callable[[], asyncio.Protocol]", self._protocol_factory
            )
            _serial_transport, serial_protocol = await serialx.create_serial_connection(
                asyncio.get_running_loop(),
                serial_factory,
                url=destination,
                baudrate=38400,
                byte_size=serialx.EIGHTBITS,
                parity=serialx.Parity.NONE,
                stopbits=serialx.StopBits.ONE,
                xonxoff=False,
                rtscts=True,
            )
            self._protocol = cast("VelbusProtocol", serial_protocol)
        except (FileNotFoundError, serialx.SerialException) as err:
            raise VelbusConnectionFailed from err
        if ctrl.is_closing():
            if self._protocol:
                self._protocol.close()
            return
        self._is_connected = True
        self._connected_event.set()
        await ctrl.notify_connection_state(True)

    async def start(self) -> None:
        """Scan the bus or load a VLP file."""
        ctrl = self.controller
        vlp_file = ctrl.vlp_file
        if vlp_file:
            vlp = VlpFile(vlp_file)
            await vlp.read()
            for mod_data in vlp.get():
                module_type = mod_data.get_type()
                if module_type is None:
                    ctrl.log.warning(
                        "Skipping VLP module at %s: unknown type %s",
                        mod_data.get_addr(),
                        mod_data.get_build(),
                    )
                    continue
                addr = mod_data.get_addr().split(",")
                decimal_addr = int(addr[0], 16)
                await ctrl.add_module(
                    decimal_addr,
                    module_type,
                    serial=mod_data.get_serial(),
                    memorymap=mod_data.get_memory(),
                    build_year=int(mod_data.get_build()[0:2]),
                    build_week=int(mod_data.get_build()[2:4]),
                )
                if len(addr) > 1:
                    ctrl.add_submodules(
                        ctrl.get_modules()[decimal_addr],
                        parse_vlp_sub_address_map(mod_data.get_addr()),
                    )
                if mod_data.get_type() == 0x45 or mod_data.get_type() == 0x5A:
                    await ctrl.get_modules()[decimal_addr].load()
                else:
                    module = ctrl.get_modules()[decimal_addr]
                    await module.load_from_vlp(mod_data)
                    await module.wait_for_status_messages()
            await ctrl.notify_scan_complete(set(ctrl.get_modules().keys()))
        else:
            await ctrl.packet_handler.scan()

    async def stop(self) -> None:
        """Stop send loop and close the protocol."""
        self._connected_event.set()
        if self._send_task and not self._send_task.done():
            self._send_task.cancel()
        if self._protocol:
            self._protocol.close()
        self._is_connected = False

    async def scan(self) -> None:
        """Rescan the Velbus bus."""
        ctrl = self.controller
        await ctrl.packet_handler.scan(True)

    async def send(self, msg: Message) -> None:
        """Enqueue a Velbus packet for transmission."""
        self._send_queue.put_nowait(
            RawMessage(
                priority=msg.priority,
                address=msg.address,
                rtr=msg.rtr,
                data=msg.data_to_binary(),
            )
        )

    async def sync_clock(self, dt: datetime.datetime | None = None) -> None:
        """Send RTC and calendar messages on the bus."""
        if dt is None:
            dt = datetime.datetime.now()
        dst = dt.dst()
        if dst is not None:
            is_dst = dst != datetime.timedelta(0)
        else:
            is_dst = bool(time.localtime().tm_isdst)
        await self.send(
            SetRealtimeClock(wday=dt.weekday(), hour=dt.hour, min=dt.minute)
        )
        await self.send(SetDate(day=dt.day, mon=dt.month, year=dt.year))
        await self.send(SetDaylightSaving(ds=not is_dst))

    def schedule_reconnect(self) -> None:
        """Retry ``connect()`` until it succeeds or auto-reconnect is off."""
        ctrl = self.controller
        if not ctrl.auto_reconnect_enabled or ctrl.closing:
            return
        ctrl.log.debug("Reconnecting to transport")
        task = asyncio.ensure_future(self._reconnect_loop())
        ctrl.add_background_task(task)

    async def _reconnect_loop(self) -> None:
        ctrl = self.controller
        retry_delay = 10
        while ctrl.auto_reconnect_enabled and not ctrl.closing:
            try:
                await ctrl.connect()
            except VelbusConnectionFailed:
                ctrl.log.warning("Reconnect failed, retrying in %ds", retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)
            else:
                return

    async def wait_on_all_messages_sent_async(self) -> None:
        """Block until the outbound queue is empty."""
        await self._send_queue.join()
