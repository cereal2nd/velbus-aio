"""Test cases for the ThermostatChannel channel class"""

from velbusaio.channels import Button, Channel, ThermostatChannel


class TestThermostatChannel:
    """Test cases for the ThermostatChannel class."""

    def test_inheritance(self, mock_module, mock_writer):
        """Test that ThermostatChannel inherits from Button."""
        thermo = ThermostatChannel(
            mock_module, 1, "Thermo", False, True, mock_writer, 0x01
        )
        assert isinstance(thermo, Button)
        assert isinstance(thermo, Channel)
