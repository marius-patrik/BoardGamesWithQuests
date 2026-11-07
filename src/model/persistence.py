"""Replay-verified bounded, atomic local game import and export."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any

from model.manager import MAX_SNAPSHOT_BYTES
from model.session import DesktopSession


class SessionFileError(ValueError):
    """A saved game cannot be safely read or written."""


def _is_symlink_or_junction(path: Path) -> bool:
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        return True
    if os.name == "nt":
        try:
            return bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
        except FileNotFoundError:
            return False
    return False


def _checked_parent(path: Path) -> Path:
    """Reject traversal and symlinked ancestors before touching user files."""
    if ".." in path.parts:
        raise SessionFileError("saved-game path cannot traverse parent directories")
    parent = path.parent
    for ancestor in (parent, *parent.parents):
        if _is_symlink_or_junction(ancestor):
            raise SessionFileError("refusing symlinked saved-game directory ancestor")
    if not parent.is_dir():
        raise SessionFileError("saved-game parent must be an existing real directory")
    return parent


def _regular_file_identity(
    path: Path, *, for_write: bool = False
) -> tuple[int, int, int, int] | None:
    try:
        found = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(found.st_mode):
        raise SessionFileError("saved-game path must be a regular non-symlinked file")
    if for_write and not stat.S_IMODE(found.st_mode) & 0o222:
        raise SessionFileError("refusing to replace read-only saved-game file")
    return found.st_dev, found.st_ino, found.st_mtime_ns, found.st_size


def _unique_properties(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise SessionFileError(f"duplicate game property: {name}")
        result[name] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SessionFileError(f"nonfinite saved-game value: {value}")


def _sync_directory(directory: Path) -> None:
    """Best-effort directory fsync after atomic replacement where supported."""
    if os.name != "posix":
        return
    try:
        descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        try:
            os.fsync(descriptor)
        except OSError:
            pass  # Filesystem-specific directory flushing may be unavailable.
    finally:
        os.close(descriptor)


def load_session(path: str | os.PathLike[str]) -> DesktopSession:
    """Read one bounded regular file and verify replay before exposing its state."""
    source = Path(path)
    try:
        _checked_parent(source)
        expected = _regular_file_identity(source)
        if expected is None:
            raise SessionFileError("saved game does not exist")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_BINARY", 0)
        )
        with os.fdopen(os.open(source, flags), "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino, opened.st_mtime_ns, opened.st_size) != expected
                or _regular_file_identity(source) != expected
            ):
                raise SessionFileError("saved game changed while opening")
            data = handle.read(MAX_SNAPSHOT_BYTES + 1)
        if len(data) > MAX_SNAPSHOT_BYTES:
            raise SessionFileError("saved game exceeds the file-size limit")
        snapshot = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_properties,
            parse_constant=_reject_constant,
        )
        return DesktopSession.recover(snapshot)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
        RecursionError,
    ) as error:
        if isinstance(error, SessionFileError):
            raise
        raise SessionFileError(f"invalid saved game: {error}") from error


def save_session(session: DesktopSession, path: str | os.PathLike[str]) -> None:
    """Verify and atomically replace the selected file, preserving failures."""
    snapshot = session.snapshot()
    try:
        encoded = (json.dumps(snapshot, sort_keys=True, allow_nan=False, indent=2) + "\n").encode(
            "utf-8"
        )
        if len(encoded) > MAX_SNAPSHOT_BYTES:
            raise SessionFileError("saved game exceeds the file-size limit")
        # The same replay contract used on import must accept every exported save.
        DesktopSession.recover(snapshot)
    except (ValueError, TypeError, RecursionError, OverflowError) as error:
        if isinstance(error, SessionFileError):
            raise
        raise SessionFileError(f"cannot save invalid game state: {error}") from error

    target = Path(path)
    parent = _checked_parent(target)
    expected = _regular_file_identity(target, for_write=True)
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=".bgwq-", suffix=".json", dir=parent)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        _checked_parent(target)
        if _regular_file_identity(target, for_write=True) != expected:
            raise SessionFileError("saved-game target changed during save")
        os.replace(temporary, target)
        temporary = None
        _sync_directory(parent)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
