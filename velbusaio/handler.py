"""
Velbus packet handler
:Author maikel punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

import asyncio
import importlib.resources
import json
import logging
import os
import pathlib
import pprint
import sys
from typing import TYPE_CHECKING, Awaitable, Callable

from aiofile import async_open
from velbusaio.vlp_reader import vlpFile
from velbusaio.vlp_reader import vlpModule



from velbusaio.command_registry import commandRegistry
from velbusaio.const import (
    SCAN_MODULEINFO_TIMEOUT_INITIAL,
    SCAN_MODULEINFO_TIMEOUT_INTERVAL,
    SCAN_MODULETYPE_TIMEOUT,
)
from velbusaio.helpers import h2, keys_exists
from velbusaio.message import Message
from velbusaio.messages.module_subtype import ModuleSubTypeMessage
from velbusaio.messages.module_type import ModuleType2Message, ModuleTypeMessage
from velbusaio.raw_message import RawMessage
from velbusaio.vlp_reader import vlpFile

if TYPE_CHECKING:
    from velbusaio.controller import Velbus


class PacketHandler:
    """
    The packetHandler class
    """

    def __init__(
        self,
        velbus: Velbus,
        one_address: int | None = None,
    ) -> None:
        self._log = logging.getLogger("velbus-handler")
        self._log.setLevel(logging.DEBUG)
        self._velbus = velbus
        self._one_address = one_address
        self._typeResponseReceived = asyncio.Event()
        self._scanLock = asyncio.Lock()
        self._modulescan_address = 0
        self._scan_complete = False
        self._scan_delay_msec = 0

    async def read_protocol_data(self):
        if sys.version_info >= (3, 13):
            with importlib.resources.path(
                __name__, "module_spec/broadcast.json"
            ) as fspath:
                async with async_open(fspath) as protocol_file:
                    self.broadcast = json.loads(await protocol_file.read())
        else:
            async with async_open(
                str(
                    importlib.resources.files(__name__.split(".")[0]).joinpath(
                        "module_spec/broadcast.json"
                    )
                )
            ) as protocol_file:
                self.broadcast = json.loads(await protocol_file.read())

    def empty_cache(self) -> bool:
        if (
            len(
                [
                    name
                    for name in os.listdir(f"{self._velbus.get_cache_dir()}")
                    if os.path.isfile(f"{self._velbus.get_cache_dir()}/{name}")
                ]
            )
            == 0
        ):
            return True
        return False

    async def scan(self, reload_cache: bool = False) -> None:
        # read the velbus project file (if available)
        vlpModules = None
        scanProgressFileName = pathlib.Path(f"{self._velbus.get_cache_dir()}/scaninprogress")
        self._modulescan_address = 0
        try:
            vlpFileName = ("MyProject.vlp")
            if os.path.isfile(vlpFileName):
                projectFile = vlpFile(vlpFileName)
                await projectFile.read();
                vlpModules = projectFile.get()
        except Exception as e:
            self._log.error(f"Project file {vlpFileName} load error {e}")

        # non-blocking check to see if the cache_dir is empty
        loop = asyncio.get_running_loop()
        if not reload_cache and await loop.run_in_executor(None, self.empty_cache):
            self._log.info("No cache yet, so forcing a bus scan")
            reload_cache = True

        # read the scan progress file to pickup interrupted uncompleted scans
        # the file will only exist during the scan process and contains the address of the last succesfull scanned module
        lastScannedAddress = 0
        if reload_cache:
            self._scan_complete = False
        elif vlpModules is None:
            try:
                with open(scanProgressFileName, "r") as file:
                    lastScannedAddress = int(file.read())
            except:
                lastScannedAddress = 254    #if there is no scaninprogress file the scan was completed 

        self._log.info("Start module scan")
        while self._modulescan_address < 254:
            address = 0
            module = None
            async with self._scanLock:
                self._modulescan_address = self._modulescan_address + 1
                address = self._modulescan_address
                if self._velbus.addr_is_submodule(address):
                    self._log.info(
                        f"Skipping submodule address {address}, already handled"
                    )
                    continue
                self._log.info(f"Start handling scan {address}")
                module = self._velbus.get_module(address)

            if self._one_address is not None and address != int(self._one_address):
                self._log.info(
                    f"Skipping address {address} as we requested to only scan one address {self._one_address}"
                )
                continue

            # construct cache file name
            cfile = pathlib.Path(f"{self._velbus.get_cache_dir()}/{address}.json")
    
            # determine if module should be handled and cleanup  cache if needed
            handleModule = False
            if vlpModules is None:
                # there is no valid project file
                # write the progress with last scanned file 

                if reload_cache:
                    handleModule = True
                    if os.path.isfile(cfile):
                        os.remove(cfile)
                else:
                    handleModule = address > lastScannedAddress or os.path.isfile(cfile) 
            else :
                # we have a valid project file
                # for now we only use the project file for module discovery
                # remove the cache file if the module is not defined in the project file
                handleModule = vlpModules.get(address)
                if os.path.isfile(cfile):
                    if reload_cache or handleModule is None:
                        os.remove(cfile)

            if handleModule:
                try:
                    self._log.info(f"Starting scan {address}")
                    self._typeResponseReceived.clear()
                    await self._velbus.sendTypeRequestMessage(address)
                    await asyncio.wait_for(
                        self._typeResponseReceived.wait(),
                        SCAN_MODULETYPE_TIMEOUT / 1000.0,
                    )
                    async with self._scanLock:
                        module = self._velbus.get_module(address)
                except asyncio.TimeoutError:
                    self._log.info(
                        f"Scan module {address} failed: not present or unavailable"
                    )
                if module is not None:
                    try:
                        self._log.debug(
                            f"Module {module.get_address()} detected: start loading"
                        )
                        await asyncio.wait_for(
                            module.load(from_cache=True),
                            SCAN_MODULEINFO_TIMEOUT_INITIAL / 1000.0,
                        )
                        self._scan_delay_msec = module.get_initial_timeout()
                        while (
                            self._scan_delay_msec > 50 and not await module.is_loaded()
                        ):
                            # self._log.debug(
                            #    f"\t... waiting {self._scan_delay_msec} is_loaded={await module.is_loaded()}"
                            # )
                            self._scan_delay_msec = self._scan_delay_msec - 50
                            await asyncio.sleep(0.05)


                        self._log.info(
                            f"Scan module {address} completed, module loaded={await module.is_loaded()}"
                        )
                    except asyncio.TimeoutError:
                        self._log.error(
                            f"Module {address} did not respond to info requests after successful type request"
                        )
            if self._modulescan_address > lastScannedAddress:
                with open(scanProgressFileName, "w") as file:
                    file.write(str(address))
                    self._modulescan_address = lastScannedAddress = address

        #remove scan progress file
        if os.path.isfile(scanProgressFileName):
            os.remove(scanProgressFileName)

        self._scan_complete = True
        self._log.info("Module scan completed")

    async def handle(self, rawmsg: RawMessage) -> None:
        """
        Handle a received packet
        """
        if rawmsg.address < 1 or rawmsg.address > 254:
            return
        if rawmsg.command is None:
            return

        priority = rawmsg.priority
        address = rawmsg.address
        rtr = rawmsg.rtr
        command_value = rawmsg.command
        data = rawmsg.data_only

        # handle module type response message
        if command_value == 0xFF and not self._scan_complete:
            tmsg: ModuleTypeMessage = ModuleTypeMessage()
            tmsg.populate(priority, address, rtr, data)
            async with self._scanLock:
                await self._handle_module_type(tmsg)
                if address == self._modulescan_address:
                    self._typeResponseReceived.set()
                else:
                    self._log.debug(
                        f"Unexpected module type message module address {address}, Velbuslink scan?"
                    )
                    self._modulescan_address = address - 1

            self._typeResponseReceived.set()

        # handle module subtype response message
        elif command_value in (0xB0, 0xA7, 0xA6) and not self._scan_complete:
            msg: ModuleSubTypeMessage = ModuleSubTypeMessage()
            msg.populate(priority, address, rtr, data)
            if command_value == 0xB0:
                msg.sub_address_offset = 0
            elif command_value == 0xA7:
                msg.sub_address_offset = 4
            elif command_value == 0xA6:
                msg.sub_address_offset = 8
            async with self._scanLock:
                self._scan_delay_msec += SCAN_MODULEINFO_TIMEOUT_INTERVAL
                self._handle_module_subtype(msg)

        # ignore broadcast
        elif command_value in self.broadcast:
            self._log.debug(
                "Received broadcast message {} from {}, ignoring".format(
                    self.broadcast[str(command_value).upper()], address
                )
            )

        # handle other messages for modules that are already scanned
        else:
            module = None
            async with self._scanLock:
                module = self._velbus.get_module(address)
            if module is not None:
                module_type = module.get_type()
                if commandRegistry.has_command(int(command_value), module_type):
                    command = commandRegistry.get_command(command_value, module_type)
                    if not command:
                        return
                    msg = command()
                    msg.populate(priority, address, rtr, data)
                    # restart the info completion time when info message received
                    if command_value in (
                        0xF0,
                        0xF1,
                        0xF2,
                        0xFB,
                        0xFE,
                        0xCC,
                    ):  # names, memory data, memory block
                        self._scan_delay_msec += SCAN_MODULEINFO_TIMEOUT_INTERVAL
                        # self._log.debug(f"Restart timeout {msg}")
                    # send the message to the modules
                    await module.on_message(msg)
                else:
                    self._log.warning(f"NOT FOUND IN command_registry: {rawmsg}")

    async def _handle_module_type(
        self, msg: ModuleTypeMessage | ModuleType2Message
    ) -> None:
        """
        load the module data
        """
        if msg is not None:
            module = self._velbus.get_module(msg.address)
            if module is None:
                # data = keys_exists(self.pdata, "ModuleTypes", h2(msg.module_type))
                # if not data:
                #    self._log.warning(f"Module not recognized: {msg.module_type}")
                #    return
                await self._velbus.add_module(
                    msg.address,
                    msg.module_type,
                    memorymap=msg.memory_map_version,
                    build_year=msg.build_year,
                    build_week=msg.build_week,
                    serial=msg.serial,
                )
            else:
                self._log.debug(
                    f"***Module already exists scanAddr={self._modulescan_address} addr={msg.address} {msg}"
                )

        # else:
        #    self._log.debug("*** handle_module_type called without response message")

    def _handle_module_subtype(self, msg: ModuleSubTypeMessage) -> None:
        module = self._velbus.get_module(msg.address)
        if module is not None:
            addrList = {
                (msg.sub_address_offset + 1): msg.sub_address_1,
                (msg.sub_address_offset + 2): msg.sub_address_2,
                (msg.sub_address_offset + 3): msg.sub_address_3,
                (msg.sub_address_offset + 4): msg.sub_address_4,
            }
            self._velbus.add_submodules(module, addrList)


#    def _channel_convert(self, module: str, channel: str, ctype: str) -> None | int:
#        data = keys_exists(
#            self.pdata, "ModuleTypes", h2(module), "ChannelNumbers", ctype
#        )
#        if data and "Map" in data and h2(channel) in data["Map"]:
#            return data["Map"][h2(channel)]
#        if data and "Convert" in data:
#            return int(channel)
#        for offset in range(0, 8):
#            if channel & (1 << offset):
#                return offset + 1
#        return None
