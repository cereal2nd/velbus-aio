"""VlpReader class.

Handles reading and parsing Velbus VLP files.
"""

import importlib.resources
import json
import logging
import sys

from aiofile import async_open
from bs4 import BeautifulSoup

from velbusaio.command_registry import MODULE_DIRECTORY
from velbusaio.helpers import h2


class VlpFile:
    """VLP file reader and parser."""

    def __init__(self, file_path) -> None:
        """Initialize VLP file reader."""
        self._file_path = file_path
        self._modules = []
        self._log = logging.getLogger("velbus-vlpFile")

    def get(self) -> dict:
        """Return the parsed modules."""
        return self._modules

    async def read(self) -> None:
        """Read and parse the VLP file."""
        async with async_open(self._file_path) as file:
            xml_content = await file.read()
        _soup = BeautifulSoup(xml_content, "xml")
        for module in _soup.find_all("Module"):
            mod = vlpModule(
                module.find("Caption").get_text(),
                module["address"],
                module["build"],
                module["serial"],
                module["type"],
                module.find("Memory").get_text(),
            )
            self._modules.append(mod)
            await mod.parse()
        self._modules.sort(key=lambda mod: mod.get_decimal_addr())

    # def dump(self) -> None:
    #    """Dump the parsed modules to the log."""
    #    for m in self._modules:
    #        print(f"Module {m.get_decimal_addr()}: {m._name}, type {m._type_id}")
    #        for key, value in m._channels.items():
    #            name = value["Name"]
    #            print(f"  {key} => {name}")


class vlpModule:
    """VLP module representation."""

    def __init__(self, name, addresses, build, serial, type, memory) -> None:
        """Initialize VLP module."""
        self._name = name
        self._addresses = addresses
        self._build = build
        self._serial = serial
        self._type = type
        self._memory = memory
        self._spec = {}
        self._channels = {}
        self._type_id = next(
            (key for key, value in MODULE_DIRECTORY.items() if value == self._type),
            None,
        )
        self._log = logging.getLogger("velbus-vlpFile")
        self._log.info(
            f"=> Created vlpModule address: {self._addresses} type: {self._type} ({self._type_id})"
        )

    def get_addr(self) -> str:
        """Get module address."""
        return self._addresses

    def get_name(self) -> str:
        """Get module name."""
        return self._name

    def get_type(self) -> int | None:
        """Get module type ID."""
        return self._type_id

    def get_serial(self) -> str:
        """Get module serial number."""
        return self._serial

    def get_memory(self) -> str:
        """Get module memory."""
        return self._memory

    def get_build(self) -> str:
        """Get module build."""
        return self._build

    def get_channels(self) -> dict:
        """Get module channels."""
        return self._channels

    def __str__(self):
        """String representation of the module."""
        return f"vlpModule(name={self._name}, addresses={self._addresses}, build={self._build}, serial={self._serial}, type={self._type})"

    def get_decimal_addr(
        self,
    ) -> int:
        """Get decimal primary module address."""
        addr = self._addresses.split(",")[0]
        return int(addr, 16)

    async def parse(self) -> None:
        """Parse the VLP module memory and extract channel names."""
        await self._load_module_spec()

        if "Memory" not in self._spec:
            self._log.debug("  => no Memory locations found")
            return

        # channel names
        self._channels = self._spec.get("Channels", {})
        for addr, chan in self._channels.items():
            self._log.debug(f" => Processing channel {addr}:")
            if ("Editable" in chan) and (chan["Editable"] == "yes"):
                self._log.debug(f"  => channel {addr} is editable, getting name")
                name = self._get_channel_name(int(addr))
                if name:
                    self._log.debug(f"  => got name '{name}' for channel {addr}")
                    self._channels[addr]["Name"] = name
                    self._channels[addr]["_is_loaded"] = True

        # extra
        self._load_extra_data()

    def _load_extra_data(self) -> None:
        """Load extra data from memory."""
        self._log.debug(" => Getting extra data")
        if "Extras" not in self._spec["Memory"]:
            self._log.debug("  => no Extra Memory locations found")
            return
        for addr, extra in self._spec["Memory"]["Extras"].items():
            byte_data = bytes.fromhex(self._read_from_memory(addr))
            self._log.debug(
                f"  => got extra data {byte_data.hex().upper()} from address {addr}"
            )
            if "Translate" in extra:
                translation_found = False
                for translate_key, translate_value in extra["Translate"].items():
                    if translate_key.startswith("%"):
                        # Binary pattern matching
                        if self._match_binary_pattern(translate_key, byte_data):
                            self._log.debug(
                                f"   => Binary pattern {translate_key} matched, value: {translate_value}"
                            )
                            self._channels[translate_value["Channel"]][
                                translate_value["SubName"]
                            ] = translate_value["Value"]
                            translation_found = True
                    else:
                        # Direct value matching (existing behavior for integer keys)
                        try:
                            int_key = int(translate_key)
                            if len(byte_data) > 0 and byte_data[0] == int_key:
                                self._log.debug(
                                    f"   => Direct match for value {int_key}: {translate_value}"
                                )
                                translation_found = True
                        except ValueError:
                            # Not an integer key, skip
                            continue
                if not translation_found:
                    self._log.error(
                        f" => No translation found for data {byte_data.hex().upper()}"
                    )

    def _match_binary_pattern(self, pattern: str, byte_data: bytes) -> bool:
        """Match a binary pattern like %......00 against byte data.

        % indicates binary pattern
        . means don't care bit
        0/1 are specific bits that must match
        """
        if not pattern.startswith("%"):
            return False

        # Remove the % prefix
        binary_pattern = pattern[1:]

        # Convert byte_data to binary string (without '0b' prefix)
        if len(byte_data) == 0:
            return False

        # Take the first byte for pattern matching
        byte_value = byte_data[0]
        binary_data = format(byte_value, "08b")

        # Check if pattern length matches
        if len(binary_pattern) != len(binary_data):
            return False

        # Check each bit position
        for _i, (pattern_bit, data_bit) in enumerate(
            zip(binary_pattern, binary_data, strict=True)
        ):
            if pattern_bit == ".":
                # Don't care bit, skip
                continue
            if pattern_bit != data_bit:
                # Specific bit must match
                return False

        return True

    def _get_channel_name(self, chan: int) -> str | None:
        """Get the name of a channel from memory."""
        if "Channels" not in self._spec["Memory"]:
            self._log.debug("  => no Channels Memory locations found")
            return None
        dchan = format(chan, "02d")
        if dchan not in self._spec["Memory"]["Channels"]:
            self._log.debug(f"  => no chan {chan} Memory locations found")
            return None
        byte_data = bytes.fromhex(
            self._read_from_memory(self._spec["Memory"]["Channels"][dchan]).replace(
                "FF", ""
            )
        )
        try:
            name = byte_data.decode("ascii")
        except UnicodeDecodeError as e:
            self._log.error(f"  => UnicodeDecodeError: {e}")
            name = byte_data
        return name

    async def _load_module_spec(self) -> None:
        """Load the module specification JSON based on type ID."""
        self._log.debug(f" => Load module spec for {self._type_id}")

        # remap VMBELx modules to unified memorymap based on build number
        # remap VMBELx TO VMBELx-20
        memmap_id = self._type_id
        if memmap_id == 0x34 and self._build >= "2524":  # VMBEL1
            memmap_id = 0x4F
        elif memmap_id == 0x35 and self._build >= "2524":  # VMBEL2
            memmap_id = 0x50
        elif memmap_id == 0x36 and self._build >= "2524":  # VMBEL4
            memmap_id = 0x51
        elif memmap_id == 0x37 and self._build >= "2438":  # VMBELO
            memmap_id = 0x52
        elif memmap_id == 0x38 and self._build >= "2524":  # VMBELPIR
            memmap_id = 0x5C
        if memmap_id != self._type_id:
            self._log.debug(
                f" => Load module spec for {self._type_id}, {self._build} => {memmap_id}"
            )

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
        """Read a range of bytes from the module memory."""
        # its a single address
        if "-" not in address_range:
            start = int(address_range, 16) * 2
            end = (int(address_range, 16) + 1) * 2
            return self._memory[start:end]
        # its a range
        start_str, end_str = address_range.split("-")
        start = int(start_str, 16) * 2
        end = (int(end_str, 16) + 1) * 2
        return self._memory[start:end]
