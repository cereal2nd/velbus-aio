"""Shared pytest fixtures for all test files"""

from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def mock_module():
    """Create a mock module for testing."""
    module = Mock()
    module.get_type.return_value = 0x01
    module.get_type_name.return_value = "TestModule"
    module.get_serial.return_value = "12345"
    module.get_addresses.return_value = [0x01, 0x02, 0x03, 0x04]
    module.get_sw_version.return_value = "1.0.0"
    module.get_name.return_value = "Test Module Name"
    module.calc_channel_offset.return_value = 0
    module.is_connected.return_value = True
    module.on_connect = Mock()
    module.remove_on_connect = Mock()
    module.on_disconnect = Mock()
    module.remove_on_disconnect = Mock()
    return module


@pytest.fixture
def mock_writer():
    """Create a mock writer for testing."""
    return AsyncMock()
