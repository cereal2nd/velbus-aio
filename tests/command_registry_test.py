#!/usr/bin/env python
import pytest

import velbusaio.command_registry
from velbusaio.command_registry import (
    MODULE_DIRECTORY,
    CommandRegistry,
    commandRegistry,
    register,
)


@pytest.fixture
def own_command_registry():
    """Ensure a clean, empty commandRegistry; even when modules are loaded as part of other tests"""
    orig_command_registry = velbusaio.command_registry.commandRegistry
    velbusaio.command_registry.commandRegistry = CommandRegistry({})
    yield
    velbusaio.command_registry.commandRegistry = orig_command_registry


@pytest.fixture
def test_module_directory():
    """Create a test module directory."""
    return {
        0x01: "TestModule1",
        0x02: "TestModule2",
        0x03: "TestModule3",
    }


class TestCommandRegistryInit:
    """Test CommandRegistry initialization."""

    def test_init_empty_directory(self):
        """Test initialization with empty module directory."""
        registry = CommandRegistry({})
        assert registry._module_directory == {}
        assert registry._default_commands == {}
        assert registry._overrides == {}

    def test_init_with_directory(self, test_module_directory):
        """Test initialization with module directory."""
        registry = CommandRegistry(test_module_directory)
        assert registry._module_directory == test_module_directory
        assert registry._default_commands == {}
        assert registry._overrides == {}


class TestCommandRegistryRegisterCommand:
    """Test register_command method."""

    def test_register_command_default(self, test_module_directory):
        """Test registering a default command."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry.register_command(0x01, TestCommand)
        assert 0x01 in registry._default_commands
        assert registry._default_commands[0x01] == TestCommand

    def test_register_command_with_module_name(self, test_module_directory):
        """Test registering a command for specific module."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry.register_command(0x05, TestCommand, "TestModule1")
        assert 0x01 in registry._overrides
        assert 0x05 in registry._overrides[0x01]
        assert registry._overrides[0x01][0x05] == TestCommand

    def test_register_command_invalid_value_negative(self, test_module_directory):
        """Test registering command with negative value raises ValueError."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        with pytest.raises(ValueError, match="Command_value should be >=0 and <=255"):
            registry.register_command(-1, TestCommand)

    def test_register_command_invalid_value_too_high(self, test_module_directory):
        """Test registering command with value > 255 raises ValueError."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        with pytest.raises(ValueError, match="Command_value should be >=0 and <=255"):
            registry.register_command(256, TestCommand)

    def test_register_command_invalid_module_name(self, test_module_directory):
        """Test registering command with unknown module name raises Exception."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        with pytest.raises(Exception, match="Module name UnknownModule not known"):
            registry.register_command(0x01, TestCommand, "UnknownModule")

    def test_register_command_boundary_values(self, test_module_directory):
        """Test registering commands at boundary values 0 and 255."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand0:
            pass

        class TestCommand255:
            pass

        registry.register_command(0, TestCommand0)
        registry.register_command(255, TestCommand255)
        assert registry._default_commands[0] == TestCommand0
        assert registry._default_commands[255] == TestCommand255


class TestCommandRegistryRegisterOverride:
    """Test _register_override method."""

    def test_register_override_new_module(self, test_module_directory):
        """Test registering override for new module type."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_override(0x05, TestCommand, 0x01)
        assert 0x01 in registry._overrides
        assert 0x05 in registry._overrides[0x01]
        assert registry._overrides[0x01][0x05] == TestCommand

    def test_register_override_existing_module(self, test_module_directory):
        """Test registering override for existing module type."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand1:
            pass

        class TestCommand2:
            pass

        registry._register_override(0x05, TestCommand1, 0x01)
        registry._register_override(0x06, TestCommand2, 0x01)
        assert registry._overrides[0x01][0x05] == TestCommand1
        assert registry._overrides[0x01][0x06] == TestCommand2

    def test_register_override_duplicate_raises_exception(self, test_module_directory):
        """Test that duplicate override registration raises exception."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand1:
            pass

        class TestCommand2:
            pass

        registry._register_override(0x05, TestCommand1, 0x01)
        with pytest.raises(
            Exception,
            match=r"double registration in command registry",
        ):
            registry._register_override(0x05, TestCommand2, 0x01)


class TestCommandRegistryRegisterDefault:
    """Test _register_default method."""

    def test_register_default_new_command(self, test_module_directory):
        """Test registering a new default command."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_default(0x10, TestCommand)
        assert 0x10 in registry._default_commands
        assert registry._default_commands[0x10] == TestCommand

    def test_register_default_duplicate_raises_exception(self, test_module_directory):
        """Test that duplicate default registration raises exception."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand1:
            pass

        class TestCommand2:
            pass

        registry._register_default(0x10, TestCommand1)
        with pytest.raises(Exception, match="double registration in command registry"):
            registry._register_default(0x10, TestCommand2)


class TestCommandRegistryHasCommand:
    """Test has_command method."""

    def test_has_command_default_exists(self, test_module_directory):
        """Test has_command returns True for existing default command."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_default(0x10, TestCommand)
        assert registry.has_command(0x10) is True

    def test_has_command_default_not_exists(self, test_module_directory):
        """Test has_command returns False for non-existing command."""
        registry = CommandRegistry(test_module_directory)
        assert registry.has_command(0x99) is False

    def test_has_command_override_exists(self, test_module_directory):
        """Test has_command returns True for existing override."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_override(0x20, TestCommand, 0x01)
        assert registry.has_command(0x20, 0x01) is True

    def test_has_command_override_different_module(self, test_module_directory):
        """Test has_command with override for different module returns False."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_override(0x20, TestCommand, 0x01)
        # Command exists for module 0x01 but not for module 0x02
        assert registry.has_command(0x20, 0x02) is False

    def test_has_command_override_priority_over_default(self, test_module_directory):
        """Test has_command finds override even when default exists."""
        registry = CommandRegistry(test_module_directory)

        class DefaultCommand:
            pass

        class OverrideCommand:
            pass

        registry._register_default(0x15, DefaultCommand)
        registry._register_override(0x15, OverrideCommand, 0x01)
        assert registry.has_command(0x15) is True
        assert registry.has_command(0x15, 0x01) is True


class TestCommandRegistryGetCommand:
    """Test get_command method."""

    def test_get_command_default_exists(self, test_module_directory):
        """Test get_command returns correct default command."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_default(0x10, TestCommand)
        result = registry.get_command(0x10)
        assert result == TestCommand

    def test_get_command_default_not_exists(self, test_module_directory):
        """Test get_command returns None for non-existing command."""
        registry = CommandRegistry(test_module_directory)
        result = registry.get_command(0x99)
        assert result is None

    def test_get_command_override_exists(self, test_module_directory):
        """Test get_command returns correct override command."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_override(0x20, TestCommand, 0x01)
        result = registry.get_command(0x20, 0x01)
        assert result == TestCommand

    def test_get_command_override_priority_over_default(self, test_module_directory):
        """Test get_command returns override when both override and default exist."""
        registry = CommandRegistry(test_module_directory)

        class DefaultCommand:
            pass

        class OverrideCommand:
            pass

        registry._register_default(0x15, DefaultCommand)
        registry._register_override(0x15, OverrideCommand, 0x01)

        # Without module type, should return default
        result = registry.get_command(0x15)
        assert result == DefaultCommand

        # With module type 0x01, should return override
        result = registry.get_command(0x15, 0x01)
        assert result == OverrideCommand

        # With different module type, should return default
        result = registry.get_command(0x15, 0x02)
        assert result == DefaultCommand

    def test_get_command_override_different_module_returns_default(
        self, test_module_directory
    ):
        """Test get_command returns default when override is for different module."""
        registry = CommandRegistry(test_module_directory)

        class DefaultCommand:
            pass

        class OverrideCommand:
            pass

        registry._register_default(0x15, DefaultCommand)
        registry._register_override(0x15, OverrideCommand, 0x01)

        # For module 0x02, should fall back to default
        result = registry.get_command(0x15, 0x02)
        assert result == DefaultCommand


class TestRegisterDecorator:
    """Test register decorator function."""

    def test_register_decorator_default(self, own_command_registry):
        """Test register decorator without module types."""

        @register(0x30)
        class TestCommand:
            pass

        assert velbusaio.command_registry.commandRegistry.has_command(0x30)
        result = velbusaio.command_registry.commandRegistry.get_command(0x30)
        assert result == TestCommand

    def test_register_decorator_with_single_module(self, own_command_registry):
        """Test register decorator with single module type."""
        # First set up a module directory
        velbusaio.command_registry.commandRegistry = CommandRegistry(
            {0x01: "TestModule"}
        )

        @register(0x35, ["TestModule"])
        class TestCommand:
            pass

        assert velbusaio.command_registry.commandRegistry.has_command(0x35, 0x01)
        result = velbusaio.command_registry.commandRegistry.get_command(0x35, 0x01)
        assert result == TestCommand

    def test_register_decorator_with_multiple_modules(self, own_command_registry):
        """Test register decorator with multiple module types."""
        velbusaio.command_registry.commandRegistry = CommandRegistry(
            {0x01: "Module1", 0x02: "Module2", 0x03: "Module3"}
        )

        @register(0x40, ["Module1", "Module2", "Module3"])
        class TestCommand:
            pass

        assert velbusaio.command_registry.commandRegistry.has_command(0x40, 0x01)
        assert velbusaio.command_registry.commandRegistry.has_command(0x40, 0x02)
        assert velbusaio.command_registry.commandRegistry.has_command(0x40, 0x03)

    def test_register_decorator_returns_class(self, own_command_registry):
        """Test that register decorator returns the original class."""

        @register(0x45)
        class TestCommand:
            test_attr = "test_value"

        # Class should still be usable normally
        assert TestCommand.test_attr == "test_value"
        instance = TestCommand()
        assert isinstance(instance, TestCommand)


class TestModuleDirectory:
    """Test MODULE_DIRECTORY constant."""

    def test_module_directory_exists(self):
        """Test that MODULE_DIRECTORY is defined and not empty."""
        assert MODULE_DIRECTORY is not None
        assert len(MODULE_DIRECTORY) > 0

    def test_module_directory_has_expected_modules(self):
        """Test that MODULE_DIRECTORY contains expected module types."""
        # Check for some well-known modules
        assert 0x01 in MODULE_DIRECTORY
        assert MODULE_DIRECTORY[0x01] == "VMB8PB"
        assert 0x20 in MODULE_DIRECTORY
        assert MODULE_DIRECTORY[0x20] == "VMBGP4"

    def test_module_directory_values_are_strings(self):
        """Test that all MODULE_DIRECTORY values are strings."""
        for key, value in MODULE_DIRECTORY.items():
            assert isinstance(key, int)
            assert isinstance(value, str)


class TestGlobalCommandRegistry:
    """Test the global commandRegistry instance."""

    def test_global_command_registry_exists(self):
        """Test that global commandRegistry is created."""
        assert commandRegistry is not None
        assert isinstance(commandRegistry, CommandRegistry)

    def test_global_command_registry_has_module_directory(self):
        """Test that global commandRegistry has MODULE_DIRECTORY."""
        assert commandRegistry._module_directory == MODULE_DIRECTORY


def test_defaults(own_command_registry):
    """Test basic registration and error handling (original test)."""

    # insert some data
    @register(1)
    class testclass:
        pass

    @register(2)
    class testclass2:
        pass

    @register(3)
    class testclass3:
        pass

    # check if double registration is raised
    with pytest.raises(Exception, match=r"double registration in command registry"):

        @register(1)
        @register(2)
        @register(3)
        class testclassR:
            pass

    # check if invalid command id
    with pytest.raises(ValueError, match=r"Command_value should be >=0 and <=255"):

        @register(0)
        @register(256)
        class testclassV:
            pass
