#!/usr/bin/env python
"""Connect, load modules, pulse a relay channel on then off after a delay."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from velbusaio.channels.relay import Relay
from velbusaio.controller import Velbus

parser = argparse.ArgumentParser(
    description="Turn a relay on, wait, then turn it off (Velbus or Signum).",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "--connect",
    help="Connection string (tls://, manager://, serial, …)",
    default="tls://192.168.1.9:27015",
)
parser.add_argument("--vlp", help="VLP file path (offline module list)", default=None)
parser.add_argument(
    "--wait",
    type=float,
    default=5.0,
    help="Seconds to leave the relay on before turn_off",
)
parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable debug logging (Velbus RX/TX or Signum propertyStatus)",
)
parser.add_argument(
    "address",
    type=lambda s: int(s, 0),
    help="Module address (decimal or 0x hex)",
)
parser.add_argument("channel", type=int, help="Relay channel number on that module")


async def main(
    connect_str: str,
    vlp_file: str | None,
    address: int,
    channel_num: int,
    wait_seconds: float,
) -> int:
    velbus = Velbus(dsn=connect_str, vlp_file=vlp_file)
    try:
        await velbus.connect()
        await velbus.start()
    except Exception:
        logging.exception("Connect or scan failed")
        return 1

    manager_backend = velbus.manager_backend
    if manager_backend is not None and not velbus.connected:
        logging.info("Waiting up to 30s for Signum Velbus gateway link...")
        await manager_backend.wait_for_bus_link(max_wait_seconds=30.0)

    if not velbus.connected:
        if manager_backend is not None and manager_backend.manager_available:
            logging.warning(
                "Velbus bus link not Connected, but Signum Manager is up; "
                "trying relay command anyway"
            )
        else:
            logging.error(
                "Not connected (Signum needs manager + gateway Connected; "
                "direct modes need a live transport)"
            )
            await velbus.stop()
            return 1

    module = velbus.get_module(address)
    if module is None:
        logging.error("No module at address %s (%#x)", address, address)
        await velbus.stop()
        return 1

    if not module.get_channels():
        logging.error(
            "Module %s has no channels (snapshot incomplete or bus offline). "
            "Check gateway Connected in Signum Manager.",
            address,
        )
        await velbus.stop()
        return 1

    channel = module.get_channels().get(channel_num)
    if channel is None:
        nums = sorted(module.get_channels())
        logging.error(
            "Module %s has no channel %s (channels: %s)",
            address,
            channel_num,
            nums,
        )
        await velbus.stop()
        return 1

    if not isinstance(channel, Relay):
        logging.error(
            "Channel %s on address %s is %s, not a relay (categories: %s)",
            channel_num,
            address,
            type(channel).__name__,
            channel.get_categories(),
        )
        await velbus.stop()
        return 1

    name = channel.get_name()
    try:
        logging.info("turn_on  module %s channel %s (%s)", address, channel_num, name)
        await channel.turn_on()
        logging.info("waiting %.1fs", wait_seconds)
        await asyncio.sleep(wait_seconds)
        logging.info("turn_off module %s channel %s (%s)", address, channel_num, name)
        await channel.turn_off()
    except Exception:
        logging.exception("Relay pulse failed")
        await velbus.stop()
        return 1

    await asyncio.sleep(0.5)
    await velbus.stop()
    return 0


def _configure_logging(verbose: bool, connect_str: str) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        style="{",
        datefmt="%H:%M:%S",
        format="{asctime} {levelname:<9} {message}",
    )
    if verbose and connect_str.startswith("manager://"):
        logging.getLogger("velbusaio.bus.manager.backend").setLevel(logging.DEBUG)


args = parser.parse_args()
_configure_logging(args.verbose, args.connect)

exit_code = asyncio.run(
    main(args.connect, args.vlp, args.address, args.channel, args.wait)
)
raise SystemExit(exit_code)
