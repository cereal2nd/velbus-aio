from __future__ import annotations

from typing import TYPE_CHECKING

import velbusaio.channels as _channels_pkg
from velbusaio.command_registry import CommandRegistryError, instantiate_command
from velbusaio.message import Message

if TYPE_CHECKING:
    from velbusaio.module import Module


def _command_message(
    code: int,
    module: Module,
    address: int,
    /,
    *args: object,
    **kwargs: object,
) -> Message:
    """Build an outbound message from the module command registry."""
    command_class = _channels_pkg.commandRegistry.get_command(code, module.get_type())
    if command_class is None:
        raise CommandRegistryError(
            f"Command {code:#04x} not registered for module type {module.get_type():#04x}"
        )
    return instantiate_command(command_class, address, *args, **kwargs)
