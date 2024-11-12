"""
:author: Maikel Punie <maikel.punie@gmail.com>
"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0x1C


@register(COMMAND_CODE, ["VMB1BLE", "VMB2BLE", "VMB1BLS","VMB2BLE-10"])
class CoverPosMessage(Message):
    """
    sent by:
    received by: VMB2BLE
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.channel = 0
        self.position = 0
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """
        :return: None
        """
        self.needs_high_priority(priority)
        self.needs_no_rtr(rtr)
        self.needs_data(data, 4)
        self.set_attributes(priority, address, rtr)
        self.channel = self.byte_to_channel(data[0])
        self.position = data[1]

    def set_defaults(self, address):
        if address is not None:
            self.set_address(address)
        self.set_high_priority()
        self.set_no_rtr()

    def data_to_binary(self):
        """
        :return: bytes
        """
        return bytes(
            [
                COMMAND_CODE,
                self.channels_to_byte([self.channel]),
                self.position,
            ]
        )
