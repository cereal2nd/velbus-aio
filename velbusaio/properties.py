"""Velbusaio property classes.

author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velbusaio.baseItem import BaseItem

if TYPE_CHECKING:
    from velbusaio.module import Module


class Property(BaseItem):
    """Base class for module-level properties."""

    def get_channel_number(self):
        """Return the channel number of this property (always 0)."""
        return 0

    def get_identifier(self) -> str:
        """Return the identifier of the entity."""
        return self.get_module_address()

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

    def __init__(self, module: Module, name: str):
        """Initialize PSU power property with per-instance current value."""
        super().__init__(module, name)
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


class SelectedProgram(Property):
    """Selected program property."""


class LightValue(Property):
    """Light value property."""

    def __init__(self, module: Module, name: str):
        """Initialize light value property with per-instance current value."""
        super().__init__(module, name)
        self._cur: float = 0.0

    def get_state(self) -> float:
        """Return the current light sensor value."""
        return round(self._cur, 2)
