"""Velbusaio property classes.

author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from velbusaio.baseItem import BaseItem
from velbusaio.command_registry import commandRegistry, instantiate_command
from velbusaio.message import Message
from velbusaio.messages.memo_text import MemoTextMessage
from velbusaio.messages.module_status import PROGRAM_SELECTION

if TYPE_CHECKING:
    from velbusaio.module import Module


class Property(BaseItem):
    """Base class for module-level properties."""

    def get_channel_number(self) -> int:
        """Return the channel number of this property (always 0)."""
        return 0

    def get_identifier(self) -> str:
        """Return the identifier of the entity."""
        return str(self.get_module_address())

    def is_sub_device(self) -> bool:
        """Return false, a property is never a subdevice."""
        return False

    def get_categories(self) -> list[str]:
        """Get the category of this property.

        default is 'sensor'.
        Override in subclass if needed.
        """
        return ["sensor"]

    def get_sensor_types(self) -> list[str]:
        """Return integrator sensor keys for this property.

        Override in subclass if needed.
        """
        if "sensor" not in self.get_categories():
            return []
        return ["measurement"]

    def get_property_key(self) -> str:
        """Return a stable, type-unique key for use in unique_id generation."""
        return type(self).__name__


class PSUPower(Property):
    """PSU Power property."""

    def __init__(
        self, module: Module, name: str, writer: Callable[[Message], Awaitable[None]]
    ):
        """Initialize PSU power property with per-instance current value."""
        super().__init__(module, name, writer)
        self._cur: float = 0.0

    def get_state(self) -> float:
        """Return the current state of the PSU power."""
        return round(self._cur, 2)

    def get_sensor_types(self) -> list[str]:
        """Return the PSU power sensor key."""
        return ["power"]


class PSUVoltage(PSUPower):
    """PSU Voltage property."""

    def get_sensor_types(self) -> list[str]:
        """Return the PSU voltage sensor key."""
        return ["voltage"]


class PSUCurrent(PSUPower):
    """PSU Current property."""

    def get_sensor_types(self) -> list[str]:
        """Return the PSU current sensor key."""
        return ["current"]


class PSULoad(PSUPower):
    """PSU Load property."""

    def get_sensor_types(self) -> list[str]:
        """Return the PSU load sensor key."""
        return ["load"]


class MemoText(Property):
    """Memo text property."""

    def get_categories(self) -> list[str]:
        """The MemoText property has no categories."""
        return []

    async def set(self, txt: str) -> None:
        """Set the memo text."""
        if not commandRegistry.has_command(0xAC, self._module.get_type()):
            raise RuntimeError("Memo text is not supported on this module type")
        msg = MemoTextMessage(self.get_module_address())
        msgcntr = 0
        for char in txt:
            msg.memo_text += char
            if len(msg.memo_text) >= 5:
                msgcntr += 5
                await self._writer(msg)
                msg = MemoTextMessage(self.get_module_address())
                msg.start = msgcntr
        if msg.memo_text:
            await self._writer(msg)


class SelectedProgram(Property):
    """A selected program property."""

    def __init__(
        self, module: Module, name: str, writer: Callable[[Message], Awaitable[None]]
    ):
        """Initialize Selected Program property with per-instance current value."""
        super().__init__(module, name, writer)
        self._selected_program_str: str | None = None

    def get_categories(self) -> list[str]:
        """Return the categories for this property."""
        return ["select"]

    def get_class(self) -> None:
        """Return the device class for this property."""
        return

    def get_options(self) -> list[str]:
        """Return the available program options for this property."""
        return list(PROGRAM_SELECTION.values())

    def get_selected_program(self) -> str | None:
        """Return the currently selected program."""
        return self._selected_program_str

    async def set_selected_program(self, program_str: str) -> None:
        """Set the currently selected program."""
        command_class = commandRegistry.get_command(0xB3, self._module.get_type())
        if command_class is None:
            raise RuntimeError("Program selection is not supported on this module type")
        index = list(PROGRAM_SELECTION.values()).index(program_str)
        program = list(PROGRAM_SELECTION.keys())[index]
        msg = instantiate_command(command_class, self.get_module_address(), program)
        await self._writer(msg)
        await self.update({"selected_program_str": program_str})


class LightValue(Property):
    """Light value property."""

    def __init__(
        self, module: Module, name: str, writer: Callable[[Message], Awaitable[None]]
    ):
        """Initialize light value property with per-instance current value."""
        super().__init__(module, name, writer)
        self._cur: float = 0.0

    def get_state(self) -> float:
        """Return the current light sensor value."""
        return round(self._cur, 2)


class BusErrorTx(Property):
    """Bus Error Transmit property."""

    def __init__(
        self, module: Module, name: str, writer: Callable[[Message], Awaitable[None]]
    ):
        """Initialize Bus Error Transmit property with per-instance current value."""
        super().__init__(module, name, writer)
        self._cur: int = 0

    def get_state(self) -> float:
        """Return the current Bus Error Transmit count."""
        return float(self._cur)


class BusErrorRx(BusErrorTx):
    """Bus Error Receive property."""


class BusErrorOff(BusErrorTx):
    """Bus Error OFF property."""
