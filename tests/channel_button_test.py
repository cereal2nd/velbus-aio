"""Test cases for the Button channel class"""

from unittest.mock import Mock, patch

import pytest

from velbusaio.channels import Button


class TestButton:
    """Test cases for the Button channel class."""

    def test_get_categories_enabled(self, mock_module, mock_writer):
        """Test button categories when enabled."""
        button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
        assert button.get_categories() == ["binary_sensor", "led", "button"]

    @pytest.mark.asyncio
    async def test_get_categories_disabled(self, mock_module, mock_writer):
        """Test button categories when disabled."""
        button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
        await button.update({"enabled": False})
        assert button.get_categories() == []

    @pytest.mark.asyncio
    async def test_is_closed(self, mock_module, mock_writer):
        """Test checking if button is closed (pressed)."""
        button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
        await button.update({"closed": True})
        assert button.is_closed()

        await button.update({"closed": False})
        assert not button.is_closed()

    @pytest.mark.asyncio
    async def test_is_on_led_on(self, mock_module, mock_writer):
        """Test checking if button LED is on."""
        button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
        await button.update({"led_state": "on"})
        assert button.is_on()

    @pytest.mark.asyncio
    async def test_is_on_led_off(self, mock_module, mock_writer):
        """Test checking if button LED is off."""
        button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
        await button.update({"led_state": "off"})
        assert not button.is_on()

    @pytest.mark.asyncio
    async def test_set_led_state_on(self, mock_module, mock_writer):
        """Test setting button LED to on."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg.leds = []
            mock_msg_class.return_value = mock_msg

            button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
            await button.set_led_state("on")

            mock_registry.get_command.assert_called_once_with(0xF6, 0x01)
            mock_writer.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_led_state_off(self, mock_module, mock_writer):
        """Test setting button LED to off."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg.leds = []
            mock_msg_class.return_value = mock_msg

            button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
            await button.set_led_state("off")

            mock_registry.get_command.assert_called_once_with(0xF5, 0x01)

    @pytest.mark.asyncio
    async def test_set_led_state_slow(self, mock_module, mock_writer):
        """Test setting button LED to slow blink."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg.leds = []
            mock_msg_class.return_value = mock_msg

            button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
            await button.set_led_state("slow")

            mock_registry.get_command.assert_called_once_with(0xF7, 0x01)

    @pytest.mark.asyncio
    async def test_set_led_state_fast(self, mock_module, mock_writer):
        """Test setting button LED to fast blink."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg.leds = []
            mock_msg_class.return_value = mock_msg

            button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
            await button.set_led_state("fast")

            mock_registry.get_command.assert_called_once_with(0xF8, 0x01)

    @pytest.mark.asyncio
    async def test_press(self, mock_module, mock_writer):
        """Test pressing button."""
        with patch("velbusaio.channels.commandRegistry") as mock_registry:
            mock_msg_class = Mock()
            mock_registry.get_command.return_value = mock_msg_class
            mock_msg = Mock()
            mock_msg.closed = []
            mock_msg.opened = []
            mock_msg_class.return_value = mock_msg

            button = Button(mock_module, 1, "Button", False, True, mock_writer, 0x01)
            await button.press()

            # Should be called twice: once for press, once for release
            assert mock_writer.call_count == 2
