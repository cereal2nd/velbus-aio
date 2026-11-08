"""Module scan, cache persistence, and channel bootstrap for Velbus modules."""

from __future__ import annotations

import json
import os
import pathlib
import struct
from typing import TYPE_CHECKING, Any, cast

import anyio

from velbusaio import channels as channels_module, properties as properties_module
from velbusaio.channels import ButtonCounter, Dimmer
from velbusaio.command_registry import commandRegistry, instantiate_command
from velbusaio.const import PRIORITY_LOW
from velbusaio.helpers import keys_exists
from velbusaio.messages.channel_name_request import (
    COMMAND_CODE as CHANNEL_NAME_REQUEST_COMMAND_CODE,
)
from velbusaio.messages.counter_status_request import CounterStatusRequestMessage
from velbusaio.messages.module_status_request import ModuleStatusRequestMessage
from velbusaio.messages.module_type_request import ModuleTypeRequestMessage
from velbusaio.messages.read_data_block_from_memory import (
    ReadDataBlockFromMemoryMessage,
)
from velbusaio.messages.read_data_from_memory import ReadDataFromMemoryMessage
from velbusaio.module_state import ModuleMixinState
from velbusaio.vlp_reader import vlpModule

if TYPE_CHECKING:
    from velbusaio.module import Module


def _coerce_cached_sub_address(addr: object) -> int:
    """Parse a sub-address stored in a module cache file."""
    if isinstance(addr, int):
        return addr
    if isinstance(addr, str):
        try:
            return int(addr)
        except ValueError:
            return int(addr, 16)
    raise TypeError(f"Unsupported cached sub-address type: {type(addr)!r}")


class ModuleScanMixin(ModuleMixinState):
    """Mixin: discovery load sequence, EEPROM/name fetch, and disk cache for :class:`~velbusaio.module.Module`."""

    async def _cache(self) -> None:
        if not self._use_cache:
            return
        cfile = pathlib.Path(f"{self._cache_dir}/{self._address}.json")
        data = json.dumps(self.to_cache(), indent=4)
        # Serialize writes per module and write atomically: dump to a
        # temp file in the same directory, then rename it onto the final
        # path. This prevents concurrent coroutines from interleaving
        # truncating writes and leaving trailing garbage behind.
        async with self._cache_lock:
            tmpfile = cfile.with_name(f"{self._address}.json.{os.getpid()}.tmp")
            async with await anyio.open_file(tmpfile, "w") as fl:
                await fl.write(data)
            await anyio.Path(tmpfile).rename(cfile)

    async def write_cache(self) -> None:
        """Persist this module's cache to disk.

        The internal cache writes are triggered by name/channel-name
        completion and by ``is_loaded()`` flipping to ``True``. A module that
        is discovered on the bus but never finishes loading (for example a
        DALI module that does not answer all of its info requests within the
        scan window) hits none of those paths and would otherwise leave no
        ``{address}.json`` behind. This method lets the scanner guarantee a
        cache file exists for every module it found.
        """
        await self._cache()

    def __getstate__(self) -> dict[str, Any]:
        """Get state for pickling."""
        d = self.__dict__
        return {
            k: d[k]
            for k in d
            if k not in {"_writer", "_log", "_controller", "_cache_lock"}
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Set state for unpickling."""
        self.__dict__ = state

    def __repr__(self) -> str:
        """Return string representation of the module."""
        return f"<{self._name} type:{self._type} address:{self._address} loaded:{self.loaded} loading:{self._is_loading} channels: {self._channels} properties: {self._properties}>"

    def __str__(self) -> str:
        """Return string representation of the module."""
        return self.__repr__()

    def to_cache(self) -> dict[str, Any]:
        """Build cache dict."""
        d: dict[str, Any] = {
            # Fall back to the human-readable module type name when the module
            # has no programmed name yet (e.g. it never finished loading). This
            # keeps the cache entry meaningful instead of an empty string.
            "name": self._name if isinstance(self._name, str) else self.get_type_name(),
            "channels": {},
            "sub_addresses": {},
            "properties": {},
        }
        for chan_num, chan in self._channels.items():
            d["channels"][chan_num] = chan.to_cache()
        for sub_num, address in self._sub_address.items():
            d["sub_addresses"][sub_num] = address
        for prop_num, prop in self._properties.items():
            d["properties"][prop_num] = prop.to_cache()
        return d

    async def _trigger_load_finished_callbacks(self) -> None:
        """Trigger all registered on load finished callbacks."""
        if self._on_module_found:
            try:
                await self._on_module_found(cast("Module", self))
            except (RuntimeError, ValueError, TypeError, AttributeError) as e:
                self._log.error(f"Error in on_module_found callback: {e}")

    async def load_from_vlp(self, vlp_data: vlpModule) -> None:
        """Initialize the module from VLP data."""
        self._is_loading = True
        self._use_cache = False
        self._name = vlp_data.get_name()
        self._data["Channels"] = vlp_data.get_channels()
        await self._load_default_channels()
        await self._load_properties()
        if self._memory is not None:
            self._memory.seed_from_vlp_hex(vlp_data.get_memory())
        for chan in self._channels.values():
            chan.set_loaded(True)
        self.loaded = True
        self._is_loading = False
        await self._request_module_status()
        await self._trigger_load_finished_callbacks()

    async def load(self, from_cache: bool = False) -> None:
        """Initialize the module."""
        # start the loading
        self._is_loading = True
        # see if we have a cache
        cache = await self._get_cache()
        self._loaded_cache = cache
        # load default channels
        await self._load_default_channels()
        await self._load_properties()

        # load the data from memory ( the stuff that we need)
        if "name" in cache and isinstance(cache["name"], str) and cache["name"] != "":
            self._name = cache["name"]
        else:
            await self._load_memory_eeprom()

        # load the sub addresses from cache if it's available
        sub_addresses_from_cache = False
        if (self._use_cache or from_cache) and "sub_addresses" in cache:
            cfile = pathlib.Path(f"{self._cache_dir}/{self._address}.json")
            try:
                for num, addr in cache["sub_addresses"].items():
                    parsed = _coerce_cached_sub_address(addr)
                    if parsed == 0xFF:
                        continue
                    self._sub_address[int(num)] = parsed
                sub_addresses_from_cache = True
            except ValueError:
                self._log.warning(
                    "Cache file for module %s has invalid sub_addresses, removing it",
                    self._address,
                )
                await anyio.Path(cfile).unlink(missing_ok=True)
        if not sub_addresses_from_cache:
            # Submit ModuleType request to trigger discovery of sub addresses.
            # Do not cache immediately here: sub addresses are populated asynchronously
            # when the response is handled; caching now could store an empty mapping.
            await self._writer(ModuleTypeRequestMessage(self._address))

        # load the module status
        # await self._request_module_status()
        # load the channel names
        if "channels" in cache:
            for num, chan in cache["channels"].items():
                # Cache keys are the canonical internal channel numbers, so they
                # must not be run through the name-map translation (which only
                # applies to channel identifiers reported in incoming messages).
                chan_num = int(num)
                if chan_num not in self._channels:
                    continue
                self._channels[chan_num].set_name(chan["name"])
                if "subdevice" in chan:
                    self._channels[chan_num].set_sub_device(chan["subdevice"])
                else:
                    self._channels[chan_num].set_sub_device(False)
                if "Unit" in chan:
                    unit_channel = self._channels[chan_num]
                    if isinstance(unit_channel, ButtonCounter):
                        unit_channel.set_unit(chan["Unit"])
                self._channels[chan_num].set_loaded(True)
        else:
            await self._request_channel_name()
        # load the module specific stuff
        self._load()
        # stop the loading
        self._is_loading = False
        await self._request_module_status()
        await self._trigger_load_finished_callbacks()

    async def _get_cache(self) -> dict[str, Any]:
        cfile = pathlib.Path(f"{self._cache_dir}/{self._address}.json")
        try:
            async with await anyio.open_file(cfile, "r") as fl:
                cache = json.loads(await fl.read())
        except OSError:
            return {}
        except (json.JSONDecodeError, KeyError, ValueError):
            cache = None
        if not isinstance(cache, dict):
            self._log.warning(
                "Cache file for module %s is corrupt, removing it",
                self._address,
            )
            await anyio.Path(cfile).unlink(missing_ok=True)
            return {}
        return cache

    async def is_loaded(self) -> bool:
        """Check if all name messages have been received."""
        # if we are loaded, just return
        if self.loaded:
            return True
        if self._is_loading:
            return False
        # Name loading is still in progress if the buffer is non-empty.
        # _name is an empty dict (initial state), None (no name spec), or a str (fully loaded).
        if self._name_buffer:
            return False
        # all channel names should be loaded
        for chan in self._channels.values():
            if not chan.is_loaded():
                return False
        # set that  we finished the module loading
        self.loaded = True
        await self._cache()
        return True

    async def _request_module_status(self) -> None:
        """Request current state of channels."""
        if "Channels" not in self._data:
            # some modules have no channels
            return
        self._log.info(f"Request module status {self._address}")

        mod_stat_req_msg = ModuleStatusRequestMessage(self._address)
        counter_msg = None
        if keys_exists(self._data, "AllChannelStatus"):
            mod_stat_req_msg.channels = self._data["AllChannelStatus"]
        else:
            for chan, chan_data in self._data["Channels"].items():
                if int(chan) < 9 and chan_data["Type"] in ("Blind", "Dimmer", "Relay"):
                    mod_stat_req_msg.channels.append(int(chan))
                if chan_data["Type"] == "ButtonCounter":
                    if counter_msg is None:
                        counter_msg = CounterStatusRequestMessage(self._address)
                    counter_msg.channels.append(int(chan))
        await self._writer(mod_stat_req_msg)
        if counter_msg is not None:
            await self._writer(counter_msg)

    async def _request_channel_name(self) -> None:
        # request the module channel names
        msg_type = commandRegistry.get_command(
            CHANNEL_NAME_REQUEST_COMMAND_CODE, self.get_type()
        )
        if msg_type is None:
            return
        msg = instantiate_command(msg_type, self._address)
        msg.priority = PRIORITY_LOW
        if keys_exists(self._data, "AllChannelStatus"):
            setattr(msg, "channels", 0xFF)
        else:
            setattr(
                msg,
                "channels",
                list(range(1, (self.number_of_channels() + 1))),
            )
        await self._writer(msg)

    async def _request_memory_name_blocks(self, memory_ranges: str) -> None:
        """Request module or sensor name data with ReadDataBlockFromMemoryMessage."""
        for block in memory_ranges.split(";"):
            addr_start_str, addr_end_str = block.split("-")
            addr_start_int = int("0x" + addr_start_str, 0)
            addr_end_int = int("0x" + addr_end_str, 0)
            current_addr = addr_start_int
            while current_addr <= addr_end_int:
                block_end = min(current_addr + 3, addr_end_int)
                addr_start = struct.unpack(">BB", struct.pack(">h", current_addr))
                block_msg = ReadDataBlockFromMemoryMessage(self._address)
                block_msg.priority = PRIORITY_LOW
                block_msg.high_address = addr_start[0]
                block_msg.low_address = addr_start[1]
                await self._writer(block_msg)
                current_addr = block_end + 1

    async def _load_memory_eeprom(self) -> None:
        """Request all needed memory addresses from the module."""
        if "Memory" not in self._data:
            self._name = None
            return

        if self._type == 0x0C:
            self._name = None
            return

        for memory_key, memory_part in self._data["Memory"].items():
            if memory_key == "Address":
                for addr_int in memory_part:
                    addr = struct.unpack(
                        ">BB", struct.pack(">h", int("0x" + addr_int, 0))
                    )
                    msg = ReadDataFromMemoryMessage(self._address)
                    msg.priority = PRIORITY_LOW
                    msg.high_address = addr[0]
                    msg.low_address = addr[1]
                    await self._writer(msg)
            elif memory_key == "ModuleName":
                if isinstance(memory_part, str):
                    await self._request_memory_name_blocks(memory_part)
            elif memory_key == "SensorName":
                if isinstance(memory_part, dict):
                    for addr_range in memory_part.values():
                        if isinstance(addr_range, str):
                            await self._request_memory_name_blocks(addr_range)
                elif isinstance(memory_part, str):
                    await self._request_memory_name_blocks(memory_part)

    async def _load_properties(self) -> None:
        """Method for per module type loading of properties."""
        if "Properties" not in self._data:
            return

        for prop, prop_data in self._data["Properties"].items():
            if "Type" not in prop_data:
                continue
            prop_type = prop_data["Type"]
            try:
                cls = getattr(properties_module, prop_type)
            except AttributeError:
                self._log.error(
                    "Unknown property type '%s' for property '%s' on module address %s",
                    prop_type,
                    prop,
                    getattr(self, "_address", "unknown"),
                )
                continue
            self._properties[prop] = cls(
                module=self,
                name=prop_data.get("Name", prop),
                writer=self._writer,
            )

    async def _load_default_channels(self) -> None:
        if "Channels" not in self._data:
            return

        for chan, chan_data in self._data["Channels"].items():
            edit = True
            sub = True
            if "Editable" not in chan_data or chan_data["Editable"] != "yes":
                edit = False
            if "Subdevice" not in chan_data or chan_data["Subdevice"] != "yes":
                sub = False
            chan_type = chan_data["Type"]
            try:
                cls = getattr(channels_module, chan_type)
            except AttributeError:
                self._log.error(
                    "Unknown channel type '%s' for channel '%s' on module address %s",
                    chan_type,
                    chan,
                    getattr(self, "_address", "unknown"),
                )
                continue

            # The spec's Channels keys are the canonical internal channel
            # numbers. The name-map translation only applies to channel
            # identifiers reported in incoming messages, not to creation.
            chan_num = int(chan)
            self._channels[chan_num] = cls(
                module=self,
                num=chan_num,
                name=chan_data["Name"],
                nameEditable=edit,
                subDevice=sub,
                writer=self._writer,
                address=self._address,
            )
            if chan_data["Type"] == "Temperature" and (
                "Thermostat" in self._data
                or (
                    "ThermostatAddr" in self._data and self._data["ThermostatAddr"] != 0
                )
            ):
                await self._update_channel(chan_num, {"thermostat": True})
            if chan_data["Type"] == "Dimmer" and "sliderScale" in self._data:
                dimmer_channel = self._channels[chan_num]
                if isinstance(dimmer_channel, Dimmer):
                    dimmer_channel.slider_scale = self._data["sliderScale"]
