#!/usr/bin/env python

import argparse
import asyncio
import logging
import sys

from velbusaio.controller import Velbus

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--connect", help="Connection string", required=True)
parser.add_argument("--address", help="Address of the module to load", required=True)
args = parser.parse_args()


async def main(connect_str: str, address: str):
    velbus = Velbus(dsn=connect_str, one_address=address)
    await velbus.connect()
    await velbus.start()
    for mod in (velbus.get_modules()).values():
        print(mod)
        print()
    await velbus.stop()


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)
asyncio.run(main(args.connect, args.address), debug=False)
