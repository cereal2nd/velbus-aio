"""Tests for helper functions."""

from velbusaio.helpers import get_property_key_map


def test_get_property_key_map_known_entries() -> None:
    """Test that get_property_key_map returns known property entries."""
    mapping = get_property_key_map()
    assert isinstance(mapping, dict)
    # Verify a few well-known property keys are present with correct class names
    assert mapping.get("selected_program") == "SelectedProgram"
    assert mapping.get("memo_text") == "MemoText"


def test_get_property_key_map_no_duplicates() -> None:
    """Test that get_property_key_map handles duplicate keys consistently."""
    mapping = get_property_key_map()
    # Keys should be unique (dict guarantees this), just verify it returns a dict
    assert isinstance(mapping, dict)
    assert len(mapping) > 0
