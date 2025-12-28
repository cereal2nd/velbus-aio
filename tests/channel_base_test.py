"""
Test cases for the base Channel class
"""

import pytest

from velbusaio.channels import Channel


class TestChannel:
    """Test cases for the base Channel class."""

    def test_init_with_editable_name(self, mock_module, mock_writer):
        """Test channel initialization with editable name."""
        channel = Channel(mock_module, 1, "Test Channel", True, True, mock_writer, 0x01)
        assert channel.get_channel_number() == 1
        assert channel.get_name() == "Test Channel"
        assert not channel.is_loaded()
        assert channel.is_sub_device()

    def test_init_with_non_editable_name(self, mock_module, mock_writer):
        """Test channel initialization with non-editable name."""
        channel = Channel(
            mock_module, 1, "Test Channel", False, False, mock_writer, 0x01
        )
        assert channel.is_loaded()
        assert not channel.is_sub_device()

    def test_get_module_type(self, mock_module, mock_writer):
        """Test getting module type."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert channel.get_module_type() == 0x01

    def test_get_module_type_name(self, mock_module, mock_writer):
        """Test getting module type name."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert channel.get_module_type_name() == "TestModule"

    def test_get_module_serial(self, mock_module, mock_writer):
        """Test getting module serial."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert channel.get_module_serial() == "12345"

    def test_get_module_address_default(self, mock_module, mock_writer):
        """Test getting module address for default channel."""
        channel = Channel(mock_module, 5, "Test", False, False, mock_writer, 0x01)
        assert channel.get_module_address() == 0x01

    def test_get_module_address_button_9_to_16(self, mock_module, mock_writer):
        """Test getting module address for button channel 9-16."""
        channel = Channel(mock_module, 10, "Test", False, False, mock_writer, 0x01)
        assert channel.get_module_address("Button") == 0x02

    def test_get_module_address_button_17_to_24(self, mock_module, mock_writer):
        """Test getting module address for button channel 17-24."""
        channel = Channel(mock_module, 18, "Test", False, False, mock_writer, 0x01)
        assert channel.get_module_address("Button") == 0x03

    def test_get_module_address_button_over_24(self, mock_module, mock_writer):
        """Test getting module address for button channel over 24."""
        channel = Channel(mock_module, 30, "Test", False, False, mock_writer, 0x01)
        assert channel.get_module_address("Button") == 0x04

    def test_get_module_sw_version(self, mock_module, mock_writer):
        """Test getting module software version."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert channel.get_module_sw_version() == "1.0.0"

    def test_get_full_name_subdevice(self, mock_module, mock_writer):
        """Test getting full name for subdevice."""
        channel = Channel(mock_module, 1, "Channel 1", False, True, mock_writer, 0x01)
        assert channel.get_full_name() == "Test Module Name (TestModule) - Channel 1"

    def test_get_full_name_not_subdevice(self, mock_module, mock_writer):
        """Test getting full name for non-subdevice."""
        channel = Channel(mock_module, 1, "Channel 1", False, False, mock_writer, 0x01)
        assert channel.get_full_name() == "Test Module Name (TestModule)"

    def test_set_name_char(self, mock_module, mock_writer):
        """Test setting individual characters in channel name."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        channel.set_name_char(0, ord("H"))
        channel.set_name_char(1, ord("e"))
        channel.set_name_char(2, ord("l"))
        channel.set_name_char(3, ord("l"))
        channel.set_name_char(4, ord("o"))
        assert channel.get_name() == "Hello"

    def test_set_name_char_extends_string(self, mock_module, mock_writer):
        """Test that set_name_char extends string with spaces if needed."""
        channel = Channel(mock_module, 1, "Hi", False, False, mock_writer, 0x01)
        channel.set_name_char(5, ord("!"))
        assert len(channel.get_name()) >= 6
        assert channel.get_name()[5] == "!"

    def test_set_name_part(self, mock_module, mock_writer):
        """Test setting name parts."""
        channel = Channel(mock_module, 1, "Test", True, False, mock_writer, 0x01)
        channel.set_name_part(1, "Hello")
        channel.set_name_part(2, "World")
        channel.set_name_part(3, "!")
        assert channel.get_name() == "HelloWorld!"
        assert channel.is_loaded()

    def test_get_channel_info(self, mock_module, mock_writer):
        """Test getting channel info dictionary."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        info = channel.get_channel_info()
        assert info["type"] == "Channel"
        assert info["num"] == 1
        assert info["name"] == "Test"
        assert "_module" not in info
        assert "_writer" not in info

    @pytest.mark.asyncio
    async def test_update(self, mock_module, mock_writer):
        """Test updating channel attributes."""
        from unittest.mock import AsyncMock

        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        callback = AsyncMock()
        channel.on_status_update(callback)

        await channel.update({"name": "Updated Name"})
        assert channel.get_name() == "Updated Name"
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_no_change(self, mock_module, mock_writer):
        """Test update with no actual change doesn't trigger callback."""
        from unittest.mock import AsyncMock

        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        callback = AsyncMock()
        channel.on_status_update(callback)

        await channel.update({"name": "Test"})
        callback.assert_not_called()

    def test_get_categories_default(self, mock_module, mock_writer):
        """Test default categories returns empty list."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert channel.get_categories() == []

    def test_on_status_update(self, mock_module, mock_writer):
        """Test adding status update callback."""
        from unittest.mock import AsyncMock

        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        callback = AsyncMock()
        channel.on_status_update(callback)
        assert callback in channel._on_status_update

    def test_remove_on_status_update(self, mock_module, mock_writer):
        """Test removing status update callback."""
        from unittest.mock import AsyncMock

        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        callback = AsyncMock()
        channel.on_status_update(callback)
        channel.remove_on_status_update(callback)
        assert callback not in channel._on_status_update

    def test_is_counter_channel_default(self, mock_module, mock_writer):
        """Test default is_counter_channel returns False."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert not channel.is_counter_channel()

    def test_is_temperature_default(self, mock_module, mock_writer):
        """Test default is_temperature returns False."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert not channel.is_temperature()

    def test_is_water_default(self, mock_module, mock_writer):
        """Test default is_water returns False."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert not channel.is_water()

    def test_to_cache(self, mock_module, mock_writer):
        """Test converting channel to cache dictionary."""
        channel = Channel(mock_module, 1, "Test", False, True, mock_writer, 0x01)
        cache = channel.to_cache()
        assert cache["name"] == "Test"
        assert cache["type"] == "Channel"
        assert cache["subdevice"] is True

    def test_is_connected(self, mock_module, mock_writer):
        """Test checking if channel is connected."""
        channel = Channel(mock_module, 1, "Test", False, False, mock_writer, 0x01)
        assert channel.is_connected()
