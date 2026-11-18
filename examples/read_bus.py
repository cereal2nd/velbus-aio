#!/usr/bin/env python

import argparse
import asyncio
import logging
import sys
from collections.abc import Awaitable, Callable

from velbusaio.controller import Velbus

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "--connect", help="Connection string", default="tls://192.168.1.9:27015"
)
parser.add_argument("--vlp", help="VLP file path", default=None)
args = parser.parse_args()


def _register_manager_channel_loggers(velbus: Velbus) -> None:
    """Log channel state changes delivered by Signum Manager WebSocket pushes."""
    for module in velbus.get_modules().values():
        address = module.get_addresses()[0]
        for channel in module.get_channels().values():

            def make_logger(mod_addr: int, ch) -> Callable[[], Awaitable[None]]:
                async def on_update() -> None:
                    logging.info(  # noqa: LOG015
                        "Signum channel update addr=%s ch=%s %s",
                        mod_addr,
                        ch.get_channel_number(),
                        ch.get_info(),
                    )

                return on_update

            channel.on_status_update(make_logger(address, channel))


async def main(connect_str: str, vlp_file: str | None):
    velbus = Velbus(dsn=connect_str, vlp_file=vlp_file)
    velbus.add_module_found_callback(on_module_found)
    velbus.add_connect_callback(on_connect)
    await velbus.connect()
    await velbus.start()
    for mod in (velbus.get_modules()).values():
        print(mod)
        print()
    if connect_str.startswith("manager://"):
        logging.getLogger("velbusaio.bus.manager.backend").setLevel(logging.DEBUG)
        _register_manager_channel_loggers(velbus)
        logging.info(  # noqa: LOG015
            "Signum mode: waiting for WebSocket propertyStatus (no raw Velbus RX logs). "
            "connected=%s",
            velbus.connected,
        )
    await asyncio.sleep(6000000000)


async def on_module_found(module):
    logging.info("============================")  # noqa: LOG015
    logging.info("Module found: %s", module)  # noqa: LOG015
    logging.info("============================")  # noqa: LOG015


async def on_connect():
    logging.info("++++++++++++++++++++++++++++++++++")  # noqa: LOG015
    logging.info("Connected to Velbus interface")  # noqa: LOG015
    logging.info("++++++++++++++++++++++++++++++++++")  # noqa: LOG015


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    style="{",
    datefmt="%H:%M:%S",
    format="{asctime} {levelname:<9} {message}",
)
logging.getLogger("asyncio").setLevel(logging.DEBUG)
asyncio.run(main(args.connect, args.vlp), debug=True)
