#!/usr/bin/env python3
"""Compare module/channel entity keys between bus/TLS and Signum Manager paths."""

from __future__ import annotations

import argparse
import asyncio
import sys
import tempfile

from velbusaio.controller import Velbus


def _entity_keys(velbus: Velbus) -> set[str]:
    keys: set[str] = set()
    for addr, module in velbus.get_modules().items():
        serial = module.serial or str(addr)
        for chan in module.get_channels().values():
            keys.add(f"{serial}-{chan.get_identifier()}")
        for prop in module.get_properties().values():
            keys.add(f"{serial}-{prop.get_identifier()}")
    return keys


async def _run(host: str, velbus_port: int, manager_port: int, token: str | None) -> int:
    cache = tempfile.mkdtemp()
    tls_dsn = f"tls://{host}:{velbus_port}"
    signum_dsn = f"manager://{host}:{manager_port}"

    bus = Velbus(dsn=tls_dsn, cache_dir=cache)
    signum = Velbus(dsn=signum_dsn, cache_dir=cache, access_token=token)

    try:
        await bus.connect()
        await bus.start()
        await signum.connect()
        await signum.start()
    finally:
        await bus.stop()
        await signum.stop()

    bus_keys = _entity_keys(bus)
    signum_keys = _entity_keys(signum)
    only_bus = bus_keys - signum_keys
    only_signum = signum_keys - bus_keys

    if not only_bus and not only_signum:
        print("No unique-id differences.")
        return 0

    if only_bus:
        print("Only on bus/TLS path:")
        for key in sorted(only_bus):
            print(f"  {key}")
    if only_signum:
        print("Only on Signum Manager path:")
        for key in sorted(only_signum):
            print(f"  {key}")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Signum hostname or IP")
    parser.add_argument(
        "--velbus-port",
        type=int,
        default=27015,
        help="Velbus TLS port (default 27015)",
    )
    parser.add_argument(
        "--manager-port",
        type=int,
        default=4201,
        help="Signum Manager HTTP port (default 4201)",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional Bearer access token for REST",
    )
    args = parser.parse_args()
    rc = asyncio.run(
        _run(args.host, args.velbus_port, args.manager_port, args.token)
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
