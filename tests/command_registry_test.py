#!/usr/bin/env python
import pytest

import velbusaio.command_registry
from velbusaio.command_registry import (
    CommandRegistryError,
    MESSAGE_CATALOG,
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
        assert registry._overrides == {}

    def test_init_with_directory(self, test_module_directory):
        """Test initialization with module directory."""
        registry = CommandRegistry(test_module_directory)
        assert registry._module_directory == test_module_directory
        assert registry._overrides == {}


class TestCommandRegistryRegisterCommand:
    """Test register_command method."""

    def test_register_command_with_module_name(self, test_module_directory):
        """Test registering a command for specific module."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry.register_command(0x05, TestCommand, "TestModule1")
        assert 0x01 in registry._overrides
        assert 0x05 in registry._overrides[0x01]
        assert registry._overrides[0x01][0x05] == TestCommand

    def test_register_command_requires_module_name(self, test_module_directory):
        """Test registering without module name raises."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        with pytest.raises(CommandRegistryError, match="requires a module_name"):
            registry.register_command(0x01, TestCommand)

    def test_register_command_invalid_value_negative(self, test_module_directory):
        """Test registering command with negative value raises ValueError."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        with pytest.raises(ValueError, match="Command_value should be >=0 and <=255"):
            registry.register_command(-1, TestCommand, "TestModule1")

    def test_register_command_invalid_value_too_high(self, test_module_directory):
        """Test registering command with value > 255 raises ValueError."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        with pytest.raises(ValueError, match="Command_value should be >=0 and <=255"):
            registry.register_command(256, TestCommand, "TestModule1")

    def test_register_command_invalid_module_name(self, test_module_directory):
        """Test registering command with unknown module name raises Exception."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        with pytest.raises(CommandRegistryError, match="Module name UnknownModule not known"):
            registry.register_command(0x01, TestCommand, "UnknownModule")

    def test_register_command_boundary_values(self, test_module_directory):
        """Test registering commands at boundary values 0 and 255."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand0:
            pass

        class TestCommand255:
            pass

        registry.register_command(0, TestCommand0, "TestModule1")
        registry.register_command(255, TestCommand255, "TestModule1")
        assert registry._overrides[0x01][0] == TestCommand0
        assert registry._overrides[0x01][255] == TestCommand255


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

    def test_register_override_idempotent_same_class(self, test_module_directory):
        """Test that re-registering the same override is a no-op."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_override(0x05, TestCommand, 0x01)
        registry._register_override(0x05, TestCommand, 0x01)
        assert registry._overrides[0x01][0x05] is TestCommand

    def test_register_override_duplicate_raises_exception(self, test_module_directory):
        """Test that duplicate override registration raises exception."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand1:
            pass

        class TestCommand2:
            pass

        registry._register_override(0x05, TestCommand1, 0x01)
        with pytest.raises(
            CommandRegistryError,
            match=r"double registration in command registry",
        ):
            registry._register_override(0x05, TestCommand2, 0x01)


class TestRegisterModuleCommands:
    """Test register_module_commands from module specs."""

    def test_register_module_commands(self, test_module_directory):
        """Test registering commands for a module from a spec mapping."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        MESSAGE_CATALOG["TestCommand"] = TestCommand
        registry.register_module_commands(0x01, {"10": "TestCommand"})
        assert registry.get_command(0x10, 0x01) is TestCommand

    def test_register_module_commands_unknown_class(self, test_module_directory):
        """Test unknown class names raise CommandRegistryError."""
        registry = CommandRegistry(test_module_directory)
        with pytest.raises(CommandRegistryError, match="Unknown message class"):
            registry.register_module_commands(0x01, {"10": "MissingMessageClass"})

    def test_register_module_commands_multiple_modules(self):
        """Test the same command class can be registered for multiple module types."""
        registry = CommandRegistry(
            {0x01: "Module1", 0x02: "Module2", 0x03: "Module3"}
        )

        class TestCommand:
            pass

        MESSAGE_CATALOG["TestCommand"] = TestCommand
        for module_type in (0x01, 0x02, 0x03):
            registry.register_module_commands(module_type, {"40": "TestCommand"})
            assert registry.get_command(0x40, module_type) is TestCommand


class TestCommandRegistryHasCommand:
    """Test has_command method."""

    def test_has_command_uninitialized_module(self, test_module_directory):
        """Test has_command returns False for uninitialized module types."""
        registry = CommandRegistry(test_module_directory)
        assert registry.has_command(0x10, 0x01) is False

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
        assert registry.has_command(0x20, 0x02) is False

    def test_has_command_spec_module_without_command(self, test_module_directory):
        """Initialized module types must not fall back to other modules."""
        registry = CommandRegistry(test_module_directory)

        class OverrideCommand:
            pass

        MESSAGE_CATALOG["OverrideCommand"] = OverrideCommand
        registry.register_module_commands(0x01, {"10": "OverrideCommand"})
        assert registry.has_command(0xF0, 0x01) is False
        assert registry.get_command(0xF0, 0x01) is None


class TestCommandRegistryGetCommand:
    """Test get_command method."""

    def test_get_command_uninitialized_module(self, test_module_directory):
        """Test get_command returns None for uninitialized module types."""
        registry = CommandRegistry(test_module_directory)
        assert registry.get_command(0x99, 0x01) is None

    def test_get_command_override_exists(self, test_module_directory):
        """Test get_command returns correct override command."""
        registry = CommandRegistry(test_module_directory)

        class TestCommand:
            pass

        registry._register_override(0x20, TestCommand, 0x01)
        result = registry.get_command(0x20, 0x01)
        assert result == TestCommand

    def test_get_command_override_different_module(self, test_module_directory):
        """Test get_command returns None when command is for another module."""
        registry = CommandRegistry(test_module_directory)

        class OverrideCommand:
            pass

        registry._register_override(0x15, OverrideCommand, 0x01)
        assert registry.get_command(0x15, 0x02) is None


class TestRegisterDecorator:
    """Test register decorator function."""

    def test_register_decorator_catalogs_class(self, own_command_registry):
        """Test register decorator adds classes to MESSAGE_CATALOG."""

        @register(0x30)
        class TestCommandCatalog:
            pass

        assert MESSAGE_CATALOG["TestCommandCatalog"] is TestCommandCatalog

    def test_register_decorator_with_single_module(self, own_command_registry):
        """Test register_module_commands for a single module type."""
        registry = CommandRegistry({0x01: "TestModule"})

        @register(0x35)
        class TestCommandSingle:
            pass

        registry.register_module_commands(0x01, {"35": "TestCommandSingle"})
        assert registry.has_command(0x35, 0x01)
        assert registry.get_command(0x35, 0x01) is TestCommandSingle

    def test_register_decorator_with_multiple_modules(self, own_command_registry):
        """Test register_module_commands for multiple module types."""
        registry = CommandRegistry(
            {0x01: "Module1", 0x02: "Module2", 0x03: "Module3"}
        )

        @register(0x40)
        class TestCommandMulti:
            pass

        for module_type in (0x01, 0x02, 0x03):
            registry.register_module_commands(module_type, {"40": "TestCommandMulti"})
            assert registry.has_command(0x40, module_type)

    def test_register_decorator_returns_class(self, own_command_registry):
        """Test that register decorator returns the original class."""

        @register(0x45)
        class TestCommandReturns:
            test_attr = "test_value"

        assert TestCommandReturns.test_attr == "test_value"
        instance = TestCommandReturns()
        assert isinstance(instance, TestCommandReturns)


class TestModuleDirectory:
    """Test MODULE_DIRECTORY constant."""

    def test_module_directory_exists(self):
        """Test that MODULE_DIRECTORY is defined and not empty."""
        assert MODULE_DIRECTORY is not None
        assert len(MODULE_DIRECTORY) > 0

    def test_module_directory_has_expected_modules(self):
        """Test that MODULE_DIRECTORY contains expected module types."""
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
    registry = CommandRegistry({0x01: "TestModule"})

    class testclass:
        pass

    class testclass2:
        pass

    class testclass3:
        pass

    registry._register_override(1, testclass, 0x01)
    registry._register_override(2, testclass2, 0x01)
    registry._register_override(3, testclass3, 0x01)

    with pytest.raises(CommandRegistryError, match=r"double registration in command registry"):
        registry._register_override(1, testclass2, 0x01)

    with pytest.raises(ValueError, match=r"Command_value should be >=0 and <=255"):
        registry.register_command(256, testclass, "TestModule")
