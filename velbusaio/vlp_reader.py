import importlib.resources
import json
import logging
import pathlib
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
            vlp_mod = vlpModule(
                module.find("Caption").get_text(),
                module["address"],
                module["build"],
                module["serial"],
                module["type"],
                module.find("Memory").get_text(),
            )
            await vlp_mod.load()
            for mod in module["address"].split(","):
                self._modules[int(mod, 16)] = vlp_mod

    async def write_cache_dir(self, cache_dir) -> None:
        for addr, mod in self._modules.items():
            cfile = pathlib.Path(f"{cache_dir}/{addr}.json")
            async with async_open(cfile, "w") as fl:
                await fl.write(json.dumps(mod.get(), indent=4))


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
        self._log = logging.getLogger("velbus-vlpModule")
        self._data = {}
        self._log.debug(
            f"vlpModule: {self._name} {self._addresses} {self._build} {self._serial} {self._type}"
        )

    async def load(self) -> None:
        await self._load_module_spec()
        await self._build_data()

    async def _build_data(self) -> None:
        self._data["name"] = self._name
        self._data["memory"] = self._memory
        self._data["channels"] = {}
        if "Channels" in self._spec:
            for chan in self._spec["Channels"]:
                self._data["channels"][int(chan)] = self.get_channel_for_cache(
                    int(chan)
                )

    def get(self) -> dict:
        return self._data

    def get_channel_name(self, chan: int) -> str | None:
        self._log.debug(f"    => get_channel_name: {chan}")
        if "Memory" not in self._spec:
            self._log.debug("      => no Memory locations found")
            return None
        if "Channels" not in self._spec["Memory"]:
            self._log.debug("      => no Channels Memory locations found")
            return None
        if h2(chan) not in self._spec["Memory"]["Channels"]:
            self._log.debug(f"     => no chan {chan} Memory locations found")
            return None
        byte_data = bytes.fromhex(
            self._read_from_memory(self._spec["Memory"]["Channels"][h2(chan)]).replace(
                "FF", ""
            )
        )
        self._log.debug(f"    => name: {byte_data.decode('ascii')}")
        return byte_data.decode("ascii")

    def get_channel_for_cache(self, chan: int) -> dict:
        self._log.debug(f"=> get_channel_for_cache: {chan}")
        if "Channels" not in self._spec:
            self._log.debug("  => no Channels found")
            return None
        if h2(chan) not in self._spec["Channels"]:
            self._log.debug(f"  => no channel {chan} found")
            return None
        chan_data = self._spec["Channels"][h2(chan)]
        if "Editable" not in chan_data or chan_data["Editable"] == "no":
            self._log.debug(f"  => channel {chan} not editable")
            name = chan_data["Name"]
        else:
            self._log.debug(f"  => channel {chan} read from memory")
            name = self.get_channel_name(chan)
        subdevice = True
        if "Subdevice" not in chan_data or chan_data["Subdevice"] != "yes":
            subdevice = False
        return {
            "name": name,
            "type": chan_data["Type"],
            "subdevice": subdevice,
        }

    async def _load_module_spec(self) -> None:
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
                        f"module_spec/{h2(self._type_id)}.json"
                    )
                )
            ) as protocol_file:
                self._spec = json.loads(await protocol_file.read())

    def _read_from_memory(self, address_range) -> str | None:
        start_str, end_str = address_range.split("-")
        start = int(start_str, 16) * 2
        end = (int(end_str, 16) + 1) * 2
        return self._memory[start:end]
