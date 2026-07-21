"""Import all message submodules so @register populates MESSAGE_CATALOG."""

from __future__ import annotations

import importlib
from pathlib import Path
import pkgutil

_PACKAGE_DIR = Path(__file__).resolve().parent
_PACKAGE_NAME = "velbusaio.messages"


def load_all_messages() -> None:
    """Import every submodule in velbusaio.messages."""
    for module_info in pkgutil.walk_packages([str(_PACKAGE_DIR)], f"{_PACKAGE_NAME}."):
        if module_info.name.endswith("._loader"):
            continue
        importlib.import_module(module_info.name)
