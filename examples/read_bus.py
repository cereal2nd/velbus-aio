#!/usr/bin/env python

import argparse
import asyncio
import logging
import sys

from velbusaio.controller import Velbus

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "--connect", help="Connection string", default="tls://192.168.1.9:27015"
)
parser.add_argument("--vlp", help="VLP file path", default=None)
args = parser.parse_args()


async def main(connect_str: str, vlp_file: str | None):
    velbus = Velbus(dsn=connect_str, vlp_file=vlp_file)
    velbus.add_module_found_callback(on_module_found)
    velbus.add_connect_callback(on_connect)
    await velbus.connect()
    await velbus.start()
    for mod in (velbus.get_modules()).values():
        print(mod)
        print()
    await asyncio.sleep(6000000000)


async def on_module_found(module):
    logging.info("============================")  # noqa: LOG015
    logging.info("Module found: %s", module)  # noqa: LOG015
    logging.info("============================")  # noqa: LOG015


async def on_connect(velbus: Velbus):
    logging.info("++++++++++++++++++++++++++++++++++")  # noqa: LOG015
    logging.info("Connected to Velbus interface %s", velbus.dsn)  # noqa: LOG015
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
