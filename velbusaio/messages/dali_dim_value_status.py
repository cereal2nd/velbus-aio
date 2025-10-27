"""
:author: Niels Laukens
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xA5


@register(
    COMMAND_CODE, ["VMBDALI", "VMBDALI-20", "VMB8DC-20", "VMB4LEDPWM-20", "VMB2DC-20"]
)
class DimValueStatus(Message):
    """
    send by: VMBDALI
    received by:
    """

    def __init__(self, address: int = None) -> None:
        super().__init__()
        self.set_defaults(address)
        self.channel: int = 0
        self.dim_values: list[int] = []
        # dim_values contain dim value of channel, channel+1, ...

    def populate(self, priority, address: int, rtr: int, data: int) -> None:
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)

        self.needs_data(data, 2)
        self.channel = data[0]
        self.dim_values = list(data[1:])

    def data_to_binary(self) -> bytes:
        return bytes(
            [
                COMMAND_CODE,
                self.channel,
            ]
        ) + bytes(self.dim_values)
