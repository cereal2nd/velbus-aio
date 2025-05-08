#!/usr/bin/env python

import argparse
import asyncio
import logging
import pprint
import sys

from velbusaio.vlp_reader import vlpFile

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--path", help="Path of the vlp file", required=True)
args = parser.parse_args()


async def main(path: str):
    vlp = vlpFile(path)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(vlp.get())


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)
asyncio.run(main(args.path))
