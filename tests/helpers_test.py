"""Tests for helper functions."""

from velbusaio.helpers import get_property_key_map


def test_get_property_key_map_known_entries() -> None:
    """Test that get_property_key_map returns known display name entries."""
    mapping = get_property_key_map()
    assert isinstance(mapping, dict)
    assert mapping.get("Selected program") == "SelectedProgram"
    assert mapping.get("Memo Text") == "MemoText"


def test_get_property_key_map_uses_display_names() -> None:
    """Test that get_property_key_map keys are display names, not spec keys."""
    mapping = get_property_key_map()
    assert isinstance(mapping, dict)
    assert len(mapping) > 0
    # Spec keys must not appear; display names must
    assert "selected_program" not in mapping
    assert "Selected program" in mapping
