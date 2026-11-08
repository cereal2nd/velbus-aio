"""Base Velbus channel type shared by all channel taxonomy classes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import string
from typing import TYPE_CHECKING, Any

from velbusaio.actions import ActionTable
from velbusaio.baseItem import BaseItem
from velbusaio.message import Message

if TYPE_CHECKING:
    from velbusaio.actions import ActionSlot
    from velbusaio.module import Module


class Channel(BaseItem):
    """A velbus channel.

    This is the basic abstract class of a velbus channel
    Each specific channel type (Relay, Dimmer, Temperature, etc.) will inherit from this class
    and implement its own specific methods and attributes.
    """

    def __init__(
        self,
        module: Module,
        num: int,
        name: str,
        nameEditable: bool,
        subDevice: bool,
        writer: Callable[[Message], Awaitable[None]],
        address: int,
    ) -> None:
        """Initialize the channel."""
        super().__init__(module, name, writer)
        self._num = num
        self._subDevice = subDevice
        if not nameEditable:
            self._is_loaded = True
        else:
            self._is_loaded = False
        self._address = address
        self._name_parts: dict[int, str] = {}

    def get_identifier(self) -> str:
        """Return the identifier of the entity."""
        if not self.is_sub_device():
            return str(self.get_module_address())
        return f"{self.get_module_address()}-{self.get_channel_number()}"

    def get_module_address(self, chan_type: str = "") -> int:
        """Return (sub)module address for channel."""
        if chan_type == "Button" and self._num > 24:
            return self._module.get_addresses()[3]
        if chan_type == "Button" and self._num > 16:
            return self._module.get_addresses()[2]
        if chan_type == "Button" and self._num > 8:
            return self._module.get_addresses()[1]
        return self._address

    def get_channel_number(self) -> int:
        """Return channel number."""
        return self._num

    def set_loaded(self, loaded: bool) -> None:
        """Set if this channel is loaded."""
        self._is_loaded = loaded

    def is_loaded(self) -> bool:
        """Is this channel loaded."""
        return self._is_loaded

    def is_counter_channel(self) -> bool:
        """Return if this channel is a counter channel."""
        return False

    def is_temperature(self) -> bool:
        """Return if this channel is a temperature sensor."""
        return False

    def set_sub_device(self, sub_device: bool) -> None:
        """Set if this channel is a subdevice."""
        self._subDevice = sub_device

    def is_sub_device(self) -> bool:
        """Return if this channel is a subdevice."""
        return self._subDevice

    def set_name_char(self, pos: int, char: int) -> None:
        """Set a char of the channel name."""
        self._is_loaded = True
        self._name_parts = {}
        # make sure the string is long enough
        while len(self._name) < int(pos):
            self._name += " "
        # store the char on correct pos
        self._name = self._name[: int(pos)] + chr(char) + self._name[int(pos) + 1 :]

    def set_name_part(self, part: int, name: str) -> bool:
        """Set a part of the channel name. Returns True if name is now complete."""
        # if int(part) not in self._name_parts:
        #    return
        self._name_parts[int(part)] = name
        if len(self._name_parts) == 3:
            self._generate_name()
            return True
        return False

    def _generate_name(self) -> None:
        """Generate the channel name if all 3 parts are received."""
        name = self._name_parts[1] + self._name_parts[2] + self._name_parts[3]
        self._name = "".join(filter(lambda x: x in string.printable, name))
        self._is_loaded = True
        self._name_parts = {}

    def __getstate__(self) -> dict[str, Any]:
        """Get channel state for pickling."""
        d = self.__dict__
        return {
            k: d[k]
            for k in d
            if k not in {"_writer", "_on_status_update", "_name_parts"}
        }

    def to_cache(self) -> dict[str, Any]:
        """Get channel state for caching."""
        dst = {
            "name": self._name,
            "type": type(self).__name__,
            "subdevice": self._subDevice,
        }
        if hasattr(self, "_Unit"):
            dst["Unit"] = self._Unit
        return dst

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore channel from cached state."""
        self.__dict__.update(state)
        self._on_status_update = []
        self._name_parts = {}

    def __repr__(self) -> str:
        """Representation of this channel."""
        items = []
        for k, v in self.__dict__.items():
            if k not in ["_module", "_writer", "_name_parts", "_class"]:
                items.append(f"{k} = {v!r}")
        return "{}[{}]".format(type(self), ", ".join(items))

    def __str__(self) -> str:
        """String representation of this channel."""
        return self.__repr__()

    def get_channel_info(self) -> dict[str, Any]:
        """Get the channel info as a dictionary."""
        data = {}
        data["type"] = self.__class__.__name__
        for key, value in self.__dict__.items():
            if key not in ["_module", "_writer", "_name_parts", "_on_status_update"]:
                data[key.replace("_", "", 1)] = value
        return data

    def get_categories(self) -> list[str]:
        """Get the categories (mainly for home-assistant).

        COMPONENT_TYPES = ["switch", "sensor", "binary_sensor", "cover", "climate", "light"]
        """
        return []

    def get_counter_state(self) -> int:
        """Return the current state of the counter."""
        raise NotImplementedError

    def get_counter_unit(self) -> str:
        """Return the unit of the counter."""
        raise NotImplementedError

    def get_max(self) -> float | None:
        """Return the maximum value."""
        raise NotImplementedError

    def get_min(self) -> float | None:
        """Return the minimum value."""
        raise NotImplementedError

    def is_water(self) -> bool:
        """Return if this channel is a water channel."""
        return False

    async def press(self) -> None:
        """Simulate a press action on this channel."""
        raise NotImplementedError

    def get_sensor_type(self) -> str | None:
        """Return the sensor type."""
        return None

    @property
    def energy(self) -> float | None:
        """Return the accumulated energy in kWh, or None if not applicable."""
        return None

    def get_action_table(self) -> ActionTable | None:
        """Return this channel's action table, if available."""
        return self._module.get_action_table(self._num)

    async def get_actions(
        self, *, refresh: bool = False, include_empty: bool = False
    ) -> list[ActionSlot]:
        """Return programmed input→output action slots for this channel."""
        table = self.get_action_table()
        if table is None:
            return []
        return await table.get_actions(refresh=refresh, include_empty=include_empty)

    async def set_action(
        self,
        *,
        source_address: int,
        action: str | int,
        source_channel: int | None = None,
        source_bit: int | None = None,
        time1: int = 0xFF,
        time2: int = 0xFF,
        time3: int = 0xFF,
        time4: int = 0xFF,
        on_release: bool = False,
        slot: int | None = None,
    ) -> ActionSlot:
        """Program an input→output action on this channel."""
        table = self.get_action_table()
        if table is None:
            raise RuntimeError(f"Channel {self._num} has no action table")
        return await table.set_action(
            source_address=source_address,
            action=action,
            source_channel=source_channel,
            source_bit=source_bit,
            time1=time1,
            time2=time2,
            time3=time3,
            time4=time4,
            on_release=on_release,
            slot=slot,
        )

    async def clear_action(self, slot: int) -> ActionSlot:
        """Clear one action slot on this channel."""
        table = self.get_action_table()
        if table is None:
            raise RuntimeError(f"Channel {self._num} has no action table")
        return await table.clear_action(slot)

    async def clear_actions_for_source(
        self,
        source_address: int,
        *,
        source_channel: int | None = None,
        source_bit: int | None = None,
    ) -> list[ActionSlot]:
        """Clear action slots matching a source input."""
        table = self.get_action_table()
        if table is None:
            return []
        return await table.clear_actions_for_source(
            source_address,
            source_channel=source_channel,
            source_bit=source_bit,
        )
