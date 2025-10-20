#!/usr/bin/env python

import argparse
import asyncio
import logging
import sys

from velbusaio.controller import Velbus

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--connect", help="Connection string", default="192.168.1.254:8445")
parser.add_argument("--vlp", help="VLP file path", default=None)
args = parser.parse_args()


async def main(connect_str: str, vlp: str):
    # SET THE connection params below
    # example via signum:
    #   velbus = Velbus("tls://192.168.1.9:27015")
    # example via plain IP
    #   velbus = Velbus("192.168.1.9:27015")
    # example via serial device
    #   velbus = Velbus("/dev/ttyAMA0")
    velbus = Velbus(dsn=connect_str, vlp_file=vlp)
    await velbus.connect()
    await velbus.start()
    for mod in (velbus.get_modules()).values():
        print(mod)
        print("")
    await velbus.stop()


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)
asyncio.run(main(args.connect, args.vlp), debug=False)
