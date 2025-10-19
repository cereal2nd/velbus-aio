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
parser.add_argument(
    "--vlp", help="VLP file path", default=None
)
args = parser.parse_args()


async def main(connect_str: str, vlp_file: str | None):
    velbus = Velbus(dsn=connect_str, vlp_file=vlp_file)
    await velbus.connect()
    await velbus.start()
    for mod in (velbus.get_modules()).values():
        print(mod)
        print("")
    await asyncio.sleep(6000000000)


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    style="{",
    datefmt="%H:%M:%S",
    format="{asctime} {levelname:<9} {message}",
)
logging.getLogger("asyncio").setLevel(logging.DEBUG)
asyncio.run(main(args.connect, args.vlp), debug=True)
