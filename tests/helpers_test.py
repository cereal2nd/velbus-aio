"""Tests for helper functions."""

from velbusaio.helpers import get_property_key_map


def test_get_property_key_map_known_entries() -> None:
    """Test that get_property_key_map returns known display name entries."""
    mapping = get_property_key_map()
    assert isinstance(mapping, dict)
    assert mapping.get("Selected program") == "SelectedProgram"
    assert mapping.get("Memo Text") == "MemoText"


def test_get_property_key_map_includes_spec_keys_and_display_names() -> None:
    """Test that both the spec key and the display name map to the class name.

    original_name may be the spec key (velbus-aio < 2026.4.1) or the display name
    (>= 2026.4.1, #181), so both forms must resolve to the same class name.
    """
    mapping = get_property_key_map()
    assert isinstance(mapping, dict)
    assert len(mapping) > 0
    assert mapping.get("selected_program") == "SelectedProgram"
    assert mapping.get("Selected program") == "SelectedProgram"
