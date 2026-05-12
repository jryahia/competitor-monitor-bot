"""
state_manager.py — JSON file-based persistence with backup on corruption.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_state(state_file: Path) -> dict[str, Any]:
    """Load state from JSON file; return empty dict on missing or corrupt file."""
    if not state_file.exists():
        return {}

    try:
        with state_file.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        backup = state_file.with_suffix(".json.bak")
        logger.warning(
            "State file corrupted (%s); backing up to %s and starting fresh.",
            exc,
            backup,
        )
        try:
            shutil.copy2(state_file, backup)
        except OSError as copy_exc:
            logger.error("Could not create backup: %s", copy_exc)
        return {}


def save_state(state: dict[str, Any], state_file: Path) -> None:
    """Atomically write state to JSON file using a temp file swap."""
    tmp = state_file.with_suffix(".json.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
        tmp.replace(state_file)
    except OSError as exc:
        logger.error("Failed to save state: %s", exc)
        raise
