"""Write Module Address And Serial Number Message.

:author: Thomas Delaet <thomas@delaet.org>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message_fields import ByteField, DeclarativeMessage, Int16Field

COMMAND_CODE = 0x6A


@register(COMMAND_CODE)
class WriteModuleAddressAndSerialNumberMessage(DeclarativeMessage):
    """Write Module Address And Serial Number Message."""

    _command_code = COMMAND_CODE
    _priority = "firmware"
    _data_length = 6

    module_type = ByteField(0, default=0x00)
    current_serial = Int16Field(1, default=0)
    module_address = ByteField(3, default=0x00)
    new_serial = Int16Field(4, default=0)
