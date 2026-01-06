"""Velbusaio property classes.

author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Awaitable

from velbusaio.baseItem import BaseItem
from velbusaio.command_registry import commandRegistry
from velbusaio.message import Message
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

    def get_sensor_type(self) -> str:
        """Get the sensor type of this property.

        Override in subclass if needed.
        """
        return type(self).__name__


class PSUPower(Property):
    """PSU Power property."""

    def __init__(
        self, module: Module, name: str, writer: callable[[Message], Awaitable[None]]
    ):
        """Initialize PSU power property with per-instance current value."""
        super().__init__(module, name, writer)
        self._cur: float = 0.0

    def get_state(self) -> float:
        """Return the current state of the PSU power."""
        return round(self._cur, 2)


class PSUVoltage(PSUPower):
    """PSU Voltage property."""


class PSUCurrent(PSUPower):
    """PSU Current property."""


class PSULoad(PSUPower):
    """PSU Load property."""


class MemoText(Property):
    """Memo text property."""

    def get_categories(self) -> list[str]:
        """The MemoText property has no categories."""
        return []

    async def set(self, txt: str) -> None:
        """Set the memo text."""
        cls = commandRegistry.get_command(0xAC, self._module.get_type())
        msg = cls(self.get_module_address())
        msgcntr = 0
        for char in txt:
            msg.memo_text += char
            if len(msg.memo_text) >= 5:
                msgcntr += 5
                await self._writer(msg)
                msg = cls(self.get_module_address())
                msg.start = msgcntr
        await self._writer(msg)


class SelectedProgram(Property):
    """A selected program property."""

    def __init__(
        self, module: Module, name: str, writer: callable[[Message], Awaitable[None]]
    ):
        """Initialize PSU power property with per-instance current value."""
        super().__init__(module, name, writer)
        self._selected_program_str = None

    def get_categories(self) -> list[str]:
        """Return the categories for this property."""
        return ["select"]

    def get_class(self) -> None:
        """Return the device class for this property."""
        return

    def get_options(self) -> list:
        """Return the available program options for this property."""
        return list(PROGRAM_SELECTION.values())

    def get_selected_program(self) -> str:
        """Return the currently selected program."""
        return self._selected_program_str

    async def set_selected_program(self, program_str: str) -> None:
        """Set the currently selected program."""
        self._selected_program_str = program_str
        command_code = 0xB3
        cls = commandRegistry.get_command(command_code, self._module.get_type())
        index = list(PROGRAM_SELECTION.values()).index(program_str)
        program = list(PROGRAM_SELECTION.keys())[index]
        msg = cls(self.get_module_address(), program)
        await self._writer(msg)


class LightValue(Property):
    """Light value property."""

    def __init__(self, module: Module, name: str, writer: callable[[object], object]):
        """Initialize light value property with per-instance current value."""
        super().__init__(module, name, writer)
        self._cur: float = 0.0

    def get_state(self) -> float:
        """Return the current light sensor value."""
        return round(self._cur, 2)
