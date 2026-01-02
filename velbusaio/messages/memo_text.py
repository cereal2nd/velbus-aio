""":author: Maikel Punie <maikel.punie@gmail.com>"""

from __future__ import annotations

from velbusaio.command_registry import register
from velbusaio.message import Message

COMMAND_CODE = 0xAC


@register(COMMAND_CODE)
class MemoTextMessage(Message):
    """send by:
    received by: VMBGPO, VMBGPOD
    """

    def __init__(self, address=None):
        Message.__init__(self)
        self.start = 0x00
        self.memo_text = ""
        self.set_defaults(address)

    def populate(self, priority, address, rtr, data):
        """:return: None"""
        self.needs_low_priority(priority)
        self.needs_no_rtr(rtr)
        self.set_attributes(priority, address, rtr)
        self.start = data[1]
        self.name = "".join([chr(x) for x in data[2:]])

    def data_to_binary(self):
        """:return: bytes"""
        while len(self.memo_text) < 5:
            self.memo_text += chr(0)
        return bytes([COMMAND_CODE, 0x00, self.start]) + bytes(self.memo_text, "utf-8")
