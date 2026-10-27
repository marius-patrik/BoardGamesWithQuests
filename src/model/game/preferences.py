"""Validated, atomic user preferences separate from immutable bundled game rules."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Any

DEFAULTS = {"board_size": 56, "show_coordinates": True}
FILENAME = "preferences.json"
MAX_PREFERENCES_BYTES = 4096


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
    if ".." in directory.parts:
        raise PreferencesError("unsafe preference directory")
    for ancestor in (directory, *directory.parents):
        if ancestor.is_symlink() or getattr(ancestor, "is_junction", lambda: False)():
            raise PreferencesError("refusing symlinked preference directory ancestor")
    if create:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        # mkdir(parents=True) can encounter a newly introduced symlink.
        _checked_directory(directory, create=False)
    elif not directory.exists():
        return directory
    if not directory.is_dir():
        raise PreferencesError("preferences must reside in a real directory")
    return directory


def _regular_file_identity(
    path: Path, *, for_write: bool = False
) -> tuple[int, int, int, int] | None:
    try:
        found = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(found.st_mode):
        raise PreferencesError("preferences target must be a regular non-symlinked file")
    if for_write and not stat.S_IMODE(found.st_mode) & 0o222:
        raise PreferencesError("refusing to replace read-only preferences file")
    return found.st_dev, found.st_ino, found.st_mtime_ns, found.st_size


def _unique_properties(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreferencesError(f"duplicate preference property: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise PreferencesError(f"nonfinite preference value: {value}")


def _sync_directory(directory: Path) -> None:
    """Flush the renamed directory entry on systems supporting directory fsync."""
    if os.name != "posix":
        return
    try:
        fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        try:
            os.fsync(fd)
        except OSError:
            pass  # Some filesystems cannot fsync directories.
    finally:
        os.close(fd)


def load_preferences(directory: Path | None = None) -> dict[str, Any]:
    """Read bounded, strictly parsed preferences; default only when absent."""
    root = Path(directory) if directory is not None else preferences_directory()
    try:
        root = _checked_directory(root, create=False)
        if not root.exists():
            return dict(DEFAULTS)
        source = root / FILENAME
        expected = _regular_file_identity(source)
        if expected is None:
            return dict(DEFAULTS)
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_BINARY", 0)
        )
        with os.fdopen(os.open(source, flags), "rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode) or (
                opened.st_dev, opened.st_ino, opened.st_mtime_ns, opened.st_size
            ) != expected or _regular_file_identity(source) != expected:
                raise PreferencesError("preferences file changed while opening")
            raw = handle.read(MAX_PREFERENCES_BYTES + 1)
        if len(raw) > MAX_PREFERENCES_BYTES:
            raise PreferencesError("preferences file exceeds the size limit")
        return validate_preferences(
            json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_unique_properties,
                parse_constant=_reject_constant,
            )
        )
    except (UnicodeError, json.JSONDecodeError, OSError) as error:
        raise PreferencesError(f"invalid saved preferences: {error}") from error


def save_preferences(data: Any, directory: Path | None = None) -> dict[str, Any]:
    """Write validated preferences to a private temporary file before replacement."""
    settings = validate_preferences(data)
    encoded = (json.dumps(settings, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    if len(encoded) > MAX_PREFERENCES_BYTES:
        raise PreferencesError("preferences file exceeds the size limit")
    root = _checked_directory(
        Path(directory) if directory is not None else preferences_directory(), create=True
    )
    target = root / FILENAME
    expected = _regular_file_identity(target, for_write=True)
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=".preferences-", dir=root)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        _checked_directory(root, create=False)
        if _regular_file_identity(target, for_write=True) != expected:
            raise PreferencesError("preferences target changed during save")
        os.replace(temporary, target)
        temporary = None
        _sync_directory(root)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
    return settings
