"""Velbusaio property classes.

author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from velbusaio.module import Module


class BaseItem(ABC):
    """Base class for properties or channels."""

    def __init__(
        self,
        module: Module,
        name: str,
    ):
        """Initialize the property."""
        self._module = module
        self._name = name
        self._on_status_update: list[Callable[[], Awaitable[None]]] = []

    @final
    def get_name(self) -> str:
        """Return the name of this item."""
        return self._name

    @final
    def get_module(self) -> Module:
        """Get the module this property belongs to."""
        return self._module

    @final
    def get_module_type(self) -> int:
        """Return module type."""
        return self._module.get_type()

    @final
    def get_module_type_name(self) -> str:
        """Return module type name."""
        return self._module.get_type_name()

    @final
    def get_module_serial(self) -> str:
        """Return module serial number."""
        return self._module.get_serial()

    @final
    def get_module_sw_version(self) -> str:
        """Return module software version."""
        return self._module.get_sw_version()

    @final
    def get_module_address(self) -> int:
        """Return module address for channel."""
        return self._module.get_address()

    @final
    def get_full_name(self) -> str:
        """Return full channel name including module name and type."""
        if self.is_sub_device():
            return f"{self._module.get_name()} ({self._module.get_type_name()}) - {self._name}"
        return f"{self._module.get_name()} ({self._module.get_type_name()})"

    @final
    def is_connected(self) -> bool:
        """Return if the module is connected."""
        return self._module.is_connected

    @final
    def __repr__(self) -> str:
        """Representation of this property."""
        items = []
        for k, v in self.__dict__.items():
            if k not in ["_module", "_class", "_on_status_update"]:
                items.append(f"{k} = {v!r}")
        return "{}[{}]".format(type(self), ", ".join(items))

    @final
    def __str__(self) -> str:
        """String representation of this property."""
        return self.__repr__()

    @abstractmethod
    def get_categories(self) -> list[str]:
        """Get the category of this property."""

    @abstractmethod
    def get_sensor_type(self) -> str:
        """Get the sensor type of this property."""

    @abstractmethod
    def is_sub_device(self) -> bool:
        """Return if this item is a subdevice."""

    @abstractmethod
    def get_identifier(self) -> str:
        """Return a unique identifier for this property."""

    @abstractmethod
    def get_channel_number(self) -> int:
        """Return the channel number of this item."""

    @final
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

    @final
    async def update(self, data: dict) -> None:
        """Set the attributes of this property."""
        changed = False
        for key, new_val in data.items():
            cur_val = getattr(self, f"_{key}", None)
            if cur_val is None or cur_val != new_val:
                setattr(self, f"_{key}", new_val)
                changed = True
        if changed:
            await self.status_update()

    @final
    async def status_update(self) -> None:
        """Call all registered status update methods."""
        for m in self._on_status_update:
            await m()

    @final
    def on_status_update(self, meth: Callable[[], Awaitable[None]]) -> None:
        """Register a method to be called on status update."""
        self._on_status_update.append(meth)

    @final
    def remove_on_status_update(self, meth: Callable[[], Awaitable[None]]) -> None:
        """Remove a method from the status update callbacks."""
        self._on_status_update.remove(meth)
