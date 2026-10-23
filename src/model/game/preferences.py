"""Validated, atomic user preferences separate from immutable bundled game rules."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

DEFAULTS = {"board_size": 56, "show_coordinates": True}
FILENAME = "preferences.json"


class PreferencesError(ValueError):
    """The preference document or its filesystem boundary is unsafe."""


def preferences_directory() -> Path:
    """Use the operating system's application-settings directory."""
    if sys.platform == "win32":
        parent = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        parent = Path.home() / "Library" / "Application Support"
    else:
        parent = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return parent / "BoardGamesWithQuests"


def validate_preferences(data: Any) -> dict[str, Any]:
    """Allow only non-executable display preferences, never rule/quest settings."""
    if not isinstance(data, dict) or set(data) != set(DEFAULTS):
        raise PreferencesError("unsupported or missing preference field")
    size, show = data["board_size"], data["show_coordinates"]
    if type(size) is not int or not 32 <= size <= 88:
        raise PreferencesError("board_size must be an integer from 32 to 88")
    if type(show) is not bool:
        raise PreferencesError("show_coordinates must be a boolean")
    return {"board_size": size, "show_coordinates": show}


def _checked_directory(directory: Path, *, create: bool) -> Path:
    if ".." in directory.parts or directory.is_symlink():
        raise PreferencesError("unsafe preference directory")
    if create:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not directory.is_dir() or directory.is_symlink():
        raise PreferencesError("preferences must reside in a real directory")
    return directory


def load_preferences(directory: Path | None = None) -> dict[str, Any]:
    """Read validated preferences; return defaults only when no file exists."""
    root = Path(directory) if directory is not None else preferences_directory()
    if not root.exists() and not root.is_symlink():
        return dict(DEFAULTS)
    root = _checked_directory(root, create=False)
    source = root / FILENAME
    if source.is_symlink():
        raise PreferencesError("refusing symlinked settings")
    if not source.exists():
        return dict(DEFAULTS)
    try:
        if source.stat().st_size > 4096:
            raise PreferencesError("preferences file exceeds the size limit")
        with source.open("r", encoding="utf-8") as handle:
            return validate_preferences(json.load(handle))
    except (UnicodeError, json.JSONDecodeError, OSError) as error:
        raise PreferencesError(f"invalid saved preferences: {error}") from error


def save_preferences(data: Any, directory: Path | None = None) -> dict[str, Any]:
    """Atomically persist strictly validated preferences without following file symlinks."""
    settings = validate_preferences(data)
    root = _checked_directory(
        Path(directory) if directory is not None else preferences_directory(), create=True
    )
    target = root / FILENAME
    if target.is_symlink():
        raise PreferencesError("refusing symlinked settings")
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=".preferences-", dir=root)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if target.is_symlink():
            raise PreferencesError("refusing symlinked settings")
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
    return settings
