"""Velbusaio property classes.

author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from velbusaio.module import Module


class Property:
    """Base class for module-level properties."""

    def __init__(
        self,
        module: Module,
        name: str,
    ):
        """Initialize the property."""
        self._module = module
        self._name = name
        self._on_status_update = []

    def get_module(self) -> Module:
        """Get the module this property belongs to."""
        return self._module

    def __repr__(self) -> str:
        """Representation of this property."""
        items = []
        for k, v in self.__dict__.items():
            if k not in ["_module", "_class", "_on_status_update"]:
                items.append(f"{k} = {v!r}")
        return "{}[{}]".format(type(self), ", ".join(items))

    def __str__(self) -> str:
        """String representation of this property."""
        return self.__repr__()

    def get_categories(self) -> list[str]:
        """Get the category of this property.

        default is 'sensor'.
        override in subclass if needed
        """
        return ["sensor"]

    def get_sensor_type(self) -> str:
        """Get the sensor type of this property.

        override in subclass if needed
        """
        return type(self).__name__

    def to_cache(self) -> dict:
        """Return a cacheable representation of this property.

        By default, all instance attributes except internal references
        like the parent module and callbacks are included.
        """
        data: dict = {}
        for key, value in self.__dict__.items():
            if key in ("_module", "_on_status_update"):
                continue
            data[key] = value
        return data

    async def update(self, data: dict) -> None:
        """Set the attributes of this property."""
        for key, new_val in data.items():
            cur_val = getattr(self, f"_{key}", None)
            if cur_val is None or cur_val != new_val:
                setattr(self, f"_{key}", new_val)
                await self.status_update()

    async def status_update(self) -> None:
        """Call all registered status update methods."""
        for m in self._on_status_update:
            await m()


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
