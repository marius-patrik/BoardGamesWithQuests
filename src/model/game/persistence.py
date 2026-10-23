"""Replay-verified bounded, atomic local game import and export."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

from model.game.manager import MAX_SNAPSHOT_BYTES
from model.game.session import DesktopSession


class SessionFileError(ValueError):
    """A saved game cannot be safely read or written."""


def _unique_properties(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise SessionFileError(f"duplicate game property: {name}")
        result[name] = value
    return result


def load_session(path: str | os.PathLike[str]) -> DesktopSession:
    """Read a chosen file and verify replay before exposing its state."""
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise SessionFileError("saved game must be a regular file")
    try:
        with source.open("rb") as file:
            data = file.read(MAX_SNAPSHOT_BYTES + 1)
        if len(data) > MAX_SNAPSHOT_BYTES:
            raise SessionFileError("saved game exceeds the file-size limit")
        snapshot = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_properties)
        return DesktopSession.recover(snapshot)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SessionFileError(f"invalid saved game: {error}") from error


def save_session(session: DesktopSession, path: str | os.PathLike[str]) -> None:
    """Atomically replace only the selected file after full JSON encoding."""
    target = Path(path)
    if target.is_symlink() or not target.parent.is_dir():
        raise SessionFileError("target must be a normal file in an existing directory")
    encoded = (
        json.dumps(session.snapshot(), sort_keys=True, allow_nan=False, indent=2) + "\n"
    ).encode("utf-8")
    if len(encoded) > MAX_SNAPSHOT_BYTES:
        raise SessionFileError("saved game exceeds the file-size limit")
    temporary: str | None = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=".bgwq-", suffix=".json", dir=target.parent)
        with os.fdopen(fd, "wb") as file:
            file.write(encoded)
            file.flush()
            os.fsync(file.fileno())
        if target.is_symlink():
            raise SessionFileError("refusing symlinked saved-game target")
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
