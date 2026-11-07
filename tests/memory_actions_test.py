"""Tests for memory backend, action tables and config helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from velbusaio.actions import (
    ActionSlot,
    ActionTable,
    bit_to_channel,
    build_action_tables,
    channel_to_bit,
    resolve_action_code,
)
from velbusaio.config import ConfigParameter, decode_name, encode_name
from velbusaio.exceptions import VelbusConfigError, VelbusMemoryTimeout
from velbusaio.memory import MemoryBackend, join_address, split_address
from velbusaio.messages.memory_data import MemoryDataMessage
from velbusaio.messages.memory_data_block import MemoryDataBlockMessage
from velbusaio.messages.read_data_block_from_memory import (
    ReadDataBlockFromMemoryMessage,
)
from velbusaio.messages.read_data_from_memory import ReadDataFromMemoryMessage
from velbusaio.messages.write_data_to_memory import WriteDataToMemoryMessage
from velbusaio.messages.write_memory_block import WriteMemoryBlockMessage


class TestAddressHelpers:
    """Tests for address split/join helpers."""

    def test_split_join_roundtrip(self):
        """Test Split/join roundtrip."""
        assert split_address(0x01EA) == (0x01, 0xEA)
        assert join_address(0x01, 0xEA) == 0x01EA


class TestNameCodec:
    """Tests for EEPROM name encode/decode."""

    def test_encode_pads_with_ff(self):
        """Test Encode pads with ff."""
        assert encode_name("Kitchen", 16) == b"Kitchen" + bytes([0xFF] * 9)

    def test_decode_stops_at_ff(self):
        """Test Decode stops at ff."""
        assert decode_name(b"Kitchen" + bytes([0xFF] * 9)) == "Kitchen"

    def test_decode_stops_at_nul(self):
        """Test Decode stops at nul."""
        assert decode_name(b"Hall\x00\xff") == "Hall"


class TestActionSlot:
    """Tests for ActionSlot encode/decode."""

    def test_empty_slot(self):
        """Test Empty slot."""
        slot = ActionSlot.empty_slot(3)
        assert slot.empty
        assert slot.to_bytes() == bytes([0xFF] * 6)

    def test_create_toggle(self):
        """Test Create toggle."""
        slot = ActionSlot.create(
            0,
            source_address=0x12,
            source_channel=3,
            action="toggle",
        )
        assert slot.source_bit == 0x04
        assert slot.action_code == 0x09
        assert slot.action_key == "toggle"
        assert slot.to_bytes() == bytes([0x12, 0x04, 0x09, 0xFF, 0xFF, 0xFF])

    def test_from_bytes(self):
        """Test From bytes."""
        slot = ActionSlot.from_bytes(1, bytes([0x05, 0x01, 0x09, 0xFF, 0xFF, 0xFF]))
        assert slot.source_address == 0x05
        assert slot.source_channel == 1
        assert slot.action_label == "Toggle"

    def test_garbage_eeprom_slot_treated_as_empty(self):
        """Uninitialized EEPROM with 0x00 action bytes is not programmed."""
        slot = ActionSlot.from_bytes(36, bytes([0xFF, 0xFF, 0x00, 0xFF, 0xFF, 0xFF]))
        assert slot.empty
        slot = ActionSlot.from_bytes(37, bytes([0x00, 0xFF, 0x00, 0xFF, 0xFF, 0xFF]))
        assert slot.empty

    def test_channel_bit_helpers(self):
        """Test Channel bit helpers."""
        assert channel_to_bit(1) == 0x01
        assert channel_to_bit(4) == 0x08
        assert bit_to_channel(0x08) == 4
        with pytest.raises(VelbusConfigError):
            channel_to_bit(9)

    def test_resolve_action_code(self):
        """Test Resolve action code."""
        assert resolve_action_code("relay_classic", "toggle") == 0x09
        assert resolve_action_code("relay_classic", 0x05) == 0x05
        with pytest.raises(VelbusConfigError):
            resolve_action_code("relay_classic", "nope")


class TestMemoryBackend:
    """Tests for paced memory read/write."""

    @pytest.mark.asyncio
    async def test_read_byte_uses_cache_and_waiter(self):
        """Test Read byte uses cache and waiter."""
        writer = AsyncMock()

        async def respond(msg):
            assert isinstance(msg, ReadDataFromMemoryMessage)
            reply = MemoryDataMessage(0x11)
            reply.high_address = msg.high_address
            reply.low_address = msg.low_address
            reply.data = 0x42
            backend.feed_message(reply)

        writer.side_effect = respond
        backend = MemoryBackend(0x11, writer, timeout=1.0)
        assert await backend.read_byte(0x00EA) == 0x42
        assert backend.get_cached(0x00EA) == 0x42
        # Second read should hit cache and not write again.
        writer.reset_mock()
        assert await backend.read_byte(0x00EA) == 0x42
        writer.assert_not_called()

    @pytest.mark.asyncio
    async def test_write_block_waits_for_ack(self):
        """Test Write block waits for ack."""
        writer = AsyncMock()

        async def respond(msg):
            assert isinstance(msg, WriteMemoryBlockMessage)
            reply = MemoryDataBlockMessage(0x11)
            reply.high_address = msg.high_address
            reply.low_address = msg.low_address
            reply.data = bytes(msg.data)
            backend.feed_message(reply)

        writer.side_effect = respond
        backend = MemoryBackend(0x11, writer, timeout=1.0)
        await backend.write_bytes(0x0000, bytes([0x12, 0x01, 0x09, 0xFF]))
        assert backend.get_cached_range(0x0000, 4) == bytes([0x12, 0x01, 0x09, 0xFF])

    @pytest.mark.asyncio
    async def test_write_byte_timeout(self):
        """Test Write byte timeout."""
        writer = AsyncMock()
        backend = MemoryBackend(0x11, writer, timeout=0.05)
        with pytest.raises(VelbusMemoryTimeout):
            await backend.write_byte(0x00EA, 0x00)


class TestActionTable:
    """Tests for ActionTable load/set/clear."""

    @pytest.mark.asyncio
    async def test_load_set_and_clear(self):
        """Test Load set and clear."""
        store: dict[int, int] = dict.fromkeys(range(0x0000, 0x00F0), 0xFF)
        writer = AsyncMock()

        async def respond(msg):
            if isinstance(msg, ReadDataBlockFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                data = bytes(store.get(addr + i, 0xFF) for i in range(4))
                reply = MemoryDataBlockMessage(0x11)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = data
                backend.feed_message(reply)
            elif isinstance(msg, ReadDataFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                reply = MemoryDataMessage(0x11)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = store.get(addr, 0xFF)
                backend.feed_message(reply)
            elif isinstance(msg, WriteMemoryBlockMessage):
                addr = join_address(msg.high_address, msg.low_address)
                for i, value in enumerate(msg.data):
                    store[addr + i] = value
                reply = MemoryDataBlockMessage(0x11)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = bytes(msg.data)
                backend.feed_message(reply)
            elif isinstance(msg, WriteDataToMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                store[addr] = msg.data
                reply = MemoryDataMessage(0x11)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = msg.data
                backend.feed_message(reply)

        writer.side_effect = respond
        backend = MemoryBackend(0x11, writer, timeout=1.0)
        table = ActionTable(
            backend,
            channel=1,
            bank=0x0000,
            noc_address=0x00EA,
        )

        slots = await table.load()
        assert len(slots) == 39
        assert all(slot.empty for slot in slots)
        assert await table.get_normal_closed() is False

        written = await table.set_action(
            source_address=0x05,
            source_channel=2,
            action="toggle",
        )
        assert written.slot == 0
        assert store[0x0000] == 0x05
        assert store[0x0001] == 0x02
        assert store[0x0002] == 0x09

        active = await table.get_actions()
        assert len(active) == 1
        assert active[0].action_key == "toggle"

        await table.clear_action(0)
        assert store[0x0000] == 0xFF
        assert await table.get_actions() == []

        await table.set_normal_closed(True)
        assert store[0x00EA] == 0x00
        assert await table.get_normal_closed(refresh=True) is True

    def test_build_action_tables_from_spec(self):
        """Test Build action tables from spec."""
        backend = MemoryBackend(0x11, AsyncMock())
        tables = build_action_tables(
            backend,
            {
                "slot_count": 39,
                "slot_size": 6,
                "actions": "relay_classic",
                "channels": {
                    "01": {"bank": "0000", "noc_address": "00EA"},
                    "02": {"bank": "0100", "noc_address": "01EA"},
                },
            },
        )
        assert set(tables) == {1, 2}
        assert tables[1].bank == 0x0000
        assert tables[2].noc_address == 0x01EA

    def test_build_minus10_spec(self):
        """Test -10 classic map uses 36 slots and NO/NC at xxD8."""
        import json
        from pathlib import Path

        spec = json.loads(
            (Path(__file__).parents[1] / "velbusaio/module_spec/48.json").read_text(encoding="utf-8")
        )["Memory"]["ActionTable"]
        tables = build_action_tables(MemoryBackend(0x48, AsyncMock()), spec)
        assert tables[1].slot_count == 36
        assert tables[1].noc_address == 0x00D8
        assert tables[5].bank == 0x0400

    @pytest.mark.asyncio
    async def test_shared_v2_table_filters_by_channel(self):
        """Test -20 shared 7-byte table filters by subject channel."""
        store: dict[int, int] = dict.fromkeys(
            range(0x00E8, 0x00E8 + 144 * 7), 0xFF
        )
        # Also NO/NC addresses
        for noc in (0x0010, 0x0024):
            store[noc] = 0xFF
        writer = AsyncMock()

        async def respond(msg):
            if isinstance(msg, ReadDataBlockFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                data = bytes(store.get(addr + i, 0xFF) for i in range(4))
                reply = MemoryDataBlockMessage(0x26)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = data
                backend.feed_message(reply)
            elif isinstance(msg, ReadDataFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                reply = MemoryDataMessage(0x26)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = store.get(addr, 0xFF)
                backend.feed_message(reply)
            elif isinstance(msg, WriteMemoryBlockMessage):
                addr = join_address(msg.high_address, msg.low_address)
                for i, value in enumerate(msg.data):
                    store[addr + i] = value
                reply = MemoryDataBlockMessage(0x26)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = bytes(msg.data)
                backend.feed_message(reply)
            elif isinstance(msg, WriteDataToMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                store[addr] = msg.data
                reply = MemoryDataMessage(0x26)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = msg.data
                backend.feed_message(reply)

        writer.side_effect = respond
        backend = MemoryBackend(0x26, writer, timeout=1.0)
        tables = build_action_tables(
            backend,
            {
                "layout": "shared",
                "bank": "00E8",
                "slot_count": 144,
                "slot_size": 7,
                "actions": "relay_v2",
                "channels": {
                    "01": {"noc_address": "0010"},
                    "02": {"noc_address": "0024"},
                },
            },
        )
        ch1 = tables[1]
        ch2 = tables[2]
        written = await ch1.set_action(
            source_address=0x05,
            source_channel=2,
            action="toggle",
        )
        assert written.slot_size == 7
        assert written.subject_channel == 1
        assert written.wire_action_byte == 0x09
        # bytes at 00E8: addr, bit, action, t1,t2,t3, subject
        assert store[0x00E8] == 0x05
        assert store[0x00E9] == 0x02
        assert store[0x00EA] == 0x09
        assert store[0x00EE] == 0x01

        assert len(await ch1.get_actions()) == 1
        assert await ch2.get_actions() == []

        await ch2.set_action(
            source_address=0x06,
            source_channel=1,
            action="on",
            on_release=True,
        )
        assert store[0x00E8 + 7] == 0x06
        assert store[0x00E8 + 7 + 2] == 0x85  # on_release | action 5
        assert store[0x00E8 + 7 + 6] == 0x02
        assert len(await ch1.get_actions()) == 1
        assert len(await ch2.get_actions()) == 1

    def test_blind_classic_five_byte_slot(self):
        """Classic blinds use 5-byte slots without a third time parameter."""
        slot = ActionSlot.create(
            0,
            source_address=0x10,
            source_channel=1,
            action="up",
            catalog_id="blind_classic",
            slot_size=5,
            time1=0x05,
        )
        assert slot.empty is False
        assert slot.to_bytes() == bytes([0x10, 0x01, 0x00, 0x05, 0xFF])
        parsed = ActionSlot.from_bytes(
            0, slot.to_bytes(), "blind_classic", slot_size=5
        )
        assert parsed.action_key == "up"
        assert parsed.time3 == 0xFF

    def test_input_classic_bitmask_subject(self):
        """Classic input slots store the subject channel as a bit mask."""
        slot = ActionSlot.create(
            0,
            source_address=0x22,
            source_channel=3,
            action="lock_closed",
            catalog_id="input_classic",
            slot_size=5,
            subject_channel=2,
            subject_encoding="param2_bitmask",
            release_bit=False,
        )
        assert slot.to_bytes() == bytes([0x22, 0x04, 0x01, 0xFF, 0x02])
        assert slot.matches_channel(2)
        assert not slot.matches_channel(1)
        assert slot.subject_channel == 2
        assert slot.on_release is False

    def test_input_v2_channel_number_subject(self):
        """-20 input slots store the subject as a channel number."""
        slot = ActionSlot.create(
            0,
            source_address=0x33,
            source_channel=1,
            action="unlock",
            catalog_id="input_v2",
            slot_size=5,
            subject_channel=8,
            subject_encoding="param2",
            release_bit=False,
        )
        assert slot.to_bytes() == bytes([0x33, 0x01, 0x05, 0xFF, 0x08])
        assert slot.matches_channel(8)
        assert slot.subject_channel == 8

    @pytest.mark.asyncio
    async def test_shared_input_bitmask_filters_by_channel(self):
        """Shared input tables with bitmasks appear on matching channels."""
        store: dict[int, int] = {}
        writer = AsyncMock()

        async def respond(msg):
            if isinstance(msg, ReadDataBlockFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                data = bytes(store.get(addr + i, 0xFF) for i in range(4))
                reply = MemoryDataBlockMessage(0x16)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = data
                backend.feed_message(reply)
            elif isinstance(msg, ReadDataFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                reply = MemoryDataMessage(0x16)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = store.get(addr, 0xFF)
                backend.feed_message(reply)
            elif isinstance(msg, WriteMemoryBlockMessage):
                addr = join_address(msg.high_address, msg.low_address)
                for i, value in enumerate(msg.data):
                    store[addr + i] = value
                reply = MemoryDataBlockMessage(0x16)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = bytes(msg.data)
                backend.feed_message(reply)
            elif isinstance(msg, WriteDataToMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                store[addr] = msg.data
                reply = MemoryDataMessage(0x16)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = msg.data
                backend.feed_message(reply)

        writer.side_effect = respond
        backend = MemoryBackend(0x16, writer, timeout=1.0)
        tables = build_action_tables(
            backend,
            {
                "layout": "shared",
                "bank": "0100",
                "slot_count": 8,
                "slot_size": 5,
                "actions": "input_classic",
                "subject_encoding": "param2_bitmask",
                "release_bit": False,
                "kind": "input",
                "channels": {"01": {}, "02": {}},
            },
        )
        written = await tables[2].set_action(
            source_address=0x11,
            source_channel=1,
            action="unlock",
        )
        assert written.slot_size == 5
        assert written.release_bit is False
        assert store[0x0100] == 0x11
        assert store[0x0102] == 0x05
        assert store[0x0104] == 0x02  # channel 2 bit
        assert len(await tables[2].get_actions()) == 1
        assert await tables[1].get_actions() == []

    @pytest.mark.asyncio
    async def test_button_channel_enable_via_reaction_time(self):
        """Disabling a button writes 0xFF to its reaction-time address."""
        from unittest.mock import MagicMock

        from velbusaio.channels import Button

        store: dict[int, int] = {0x0080: 0x05}
        writer = AsyncMock()

        async def respond(msg):
            if isinstance(msg, ReadDataFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                reply = MemoryDataMessage(0x16)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = store.get(addr, 0xFF)
                backend.feed_message(reply)
            elif isinstance(msg, WriteDataToMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                store[addr] = msg.data
                reply = MemoryDataMessage(0x16)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = msg.data
                backend.feed_message(reply)

        writer.side_effect = respond
        backend = MemoryBackend(0x16, writer, timeout=1.0)
        module = MagicMock()
        module.get_channel_enable_spec.return_value = {
            "address": 0x0080,
            "disabled_value": 0xFF,
            "enabled_value": 0x05,
        }
        module.get_memory.return_value = backend
        button = Button(module, 1, "PB1", True, False, writer, 0x16)

        assert await button.get_channel_enabled(refresh=True) is True
        await button.set_channel_enabled(False)
        assert store[0x0080] == 0xFF
        assert button.is_enabled() is False
        await button.set_channel_enabled(True)
        assert store[0x0080] == 0x05
        assert button.is_enabled() is True

    @pytest.mark.asyncio
    async def test_shared_dimmer_v2_subject_in_param3(self):
        """-20 dimmers store the subject channel in param3 low bits."""
        store: dict[int, int] = {}
        writer = AsyncMock()

        async def respond(msg):
            if isinstance(msg, ReadDataBlockFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                data = bytes(store.get(addr + i, 0xFF) for i in range(4))
                reply = MemoryDataBlockMessage(0x24)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = data
                backend.feed_message(reply)
            elif isinstance(msg, ReadDataFromMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                reply = MemoryDataMessage(0x24)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = store.get(addr, 0xFF)
                backend.feed_message(reply)
            elif isinstance(msg, WriteMemoryBlockMessage):
                addr = join_address(msg.high_address, msg.low_address)
                for i, value in enumerate(msg.data):
                    store[addr + i] = value
                reply = MemoryDataBlockMessage(0x24)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = bytes(msg.data)
                backend.feed_message(reply)
            elif isinstance(msg, WriteDataToMemoryMessage):
                addr = join_address(msg.high_address, msg.low_address)
                store[addr] = msg.data
                reply = MemoryDataMessage(0x24)
                reply.high_address = msg.high_address
                reply.low_address = msg.low_address
                reply.data = msg.data
                backend.feed_message(reply)

        writer.side_effect = respond
        backend = MemoryBackend(0x24, writer, timeout=1.0)
        tables = build_action_tables(
            backend,
            {
                "layout": "shared",
                "bank": "0068",
                "slot_count": 8,
                "slot_size": 6,
                "actions": "dimmer_v2",
                "subject_encoding": "param3_low3",
                "channels": {"01": {}, "02": {}},
            },
        )
        written = await tables[2].set_action(
            source_address=0x11,
            source_channel=1,
            action="toggle",
        )
        assert written.slot_size == 6
        assert written.subject_channel == 2
        assert store[0x0068] == 0x11
        assert store[0x006A] == 0x2E  # toggle = 46
        assert store[0x006D] == 0x02  # channel in low bits
        assert await tables[1].get_actions() == []
        assert len(await tables[2].get_actions()) == 1


class TestConfigParameter:
    """Tests for ConfigParameter validation."""

    @pytest.mark.asyncio
    async def test_text_and_select(self):
        """Test Text and select."""
        values = {"name": "Relay", "contact": "NO"}

        async def get_name():
            return values["name"]

        async def set_name(value):
            values["name"] = value

        async def get_contact():
            return values["contact"]

        async def set_contact(value):
            values["contact"] = value

        name = ConfigParameter(
            key="name",
            label="Channel name",
            kind="text",
            getter=get_name,
            setter=set_name,
            max_length=16,
        )
        contact = ConfigParameter(
            key="contact",
            label="Contact",
            kind="select",
            getter=get_contact,
            setter=set_contact,
            options=["NO", "NC"],
        )
        await name.set_value("Kitchen")
        assert await name.get_value() == "Kitchen"
        with pytest.raises(VelbusConfigError):
            await name.set_value("x" * 20)
        await contact.set_value("NC")
        assert await contact.get_value() == "NC"
        with pytest.raises(VelbusConfigError):
            await contact.set_value("maybe")
