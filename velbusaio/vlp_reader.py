import importlib.resources
import json
import logging
import sys

from aiofile import async_open
from bs4 import BeautifulSoup

from velbusaio.command_registry import MODULE_DIRECTORY
from velbusaio.helpers import h2


class vlpFile:

    def __init__(self, file_path) -> None:
        self._file_path = file_path
        self._modules = {}
        self._log = logging.getLogger("velbus-vlpFile")

    def get(self) -> dict:
        return self._modules

    async def read(self) -> None:
        with open(self._file_path) as file:
            xml_content = file.read()
        _soup = BeautifulSoup(xml_content, "xml")
        for module in _soup.find_all("Module"):
            self._modules[module["address"]] = vlpModule(
                module.find("Caption").get_text(),
                module["address"],
                module["build"],
                module["serial"],
                module["type"],
                module.find("Memory").get_text(),
            )
            await self._modules[module["address"]].load_module_spec()
            print(self._modules[module["address"]].get_channel_name(1))
            print(self._modules[module["address"]].get_channel_name(2))
            print(self._modules[module["address"]].get_channel_name(3))
            print(self._modules[module["address"]].get_channel_name(4))
            print(self._modules[module["address"]].get_channel_name(5))
            print(self._modules[module["address"]].get_channel_name(10))


class vlpModule:

    def __init__(self, name, addresses, build, serial, type, memory) -> None:
        self._name = name
        self._addresses = addresses
        self._build = build
        self._serial = serial
        self._type = type
        self._memory = memory
        self._spec = {}
        self._type_id = next(
            (key for key, value in MODULE_DIRECTORY.items() if value == self._type),
            None,
        )
        self._log = logging.getLogger("velbus-vlpFile")

    def get(self) -> dict:
        return {
            "name": self._name,
            "addresses": self._addresses,
            "build": self._build,
            "serial": self._serial,
            "type": self._type,
            "memory": self._memory,
        }

    def get_name(self) -> str:
        return self._name

    def get_channel_name(self, chan: int) -> str | None:
        self._log.debug(f"get_channel_name: {chan}")
        if "Memory" not in self._spec:
            self._log.debug(" => no Memory locations found")
            return None
        if "Channels" not in self._spec["Memory"]:
            self._log.debug(" => no Channels Memory locations found")
            return None
        if h2(chan) not in self._spec["Memory"]["Channels"]:
            self._log.debug(f" => no chan {chan} Memory locations found")
            return None
        byte_data = bytes.fromhex(
            self._read_from_memory(self._spec["Memory"]["Channels"][h2(chan)]).replace(
                "FF", ""
            )
        )
        return byte_data.decode("ascii")

    async def load_module_spec(self) -> None:
        if sys.version_info >= (3, 13):
            with importlib.resources.path(
                __name__, f"module_spec/{h2(self._type_id)}.json"
            ) as fspath:
                async with async_open(fspath) as protocol_file:
                    self._spec = json.loads(await protocol_file.read())
        else:
            async with async_open(
                str(
                    importlib.resources.files(__name__.split(".")[0]).joinpath(
                        f"module_spec/{h2(self._type)}.json"
                    )
                )
            ) as protocol_file:
                self._spec = json.loads(await protocol_file.read())

    def _read_from_memory(self, address_range) -> str | None:
        start_str, end_str = address_range.split("-")
        start = int(start_str, 16) * 2
        end = (int(end_str, 16) + 1) * 2
        return self._memory[start:end]
