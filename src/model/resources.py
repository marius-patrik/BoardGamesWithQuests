"""Resolve the single trusted game-definition data root in every distribution mode."""

from __future__ import annotations

import hashlib
import json
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
import sys


def bundled_games_root() -> Traversable:
    """Locate shipped JSON definitions in source, installed and frozen applications.

    The root-level games/ directory is mapped into the installed `games` namespace
    by setuptools. PyInstaller instead places its immutable data under _MEIPASS.
    Missing resources are fatal; no user-writable or working-directory fallback
    can silently replace the bundled rulebooks.
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if not isinstance(base, str):
            raise FileNotFoundError("frozen application has no resource base")
        root: Traversable = Path(base) / "games"
    else:
        root = resources.files("games")
    if not root.is_dir():
        raise FileNotFoundError("bundled games directory is missing")
    if getattr(sys, "frozen", False):
        try:
            manifest = json.loads(root.joinpath("manifest.json").read_text(encoding="utf-8"))
            hashes = manifest["files"]
            if manifest["version"] != 1 or not isinstance(hashes, dict) or not hashes:
                raise ValueError("unsupported frozen resource manifest")
            for relative, digest in hashes.items():
                if (
                    not isinstance(relative, str)
                    or not isinstance(digest, str)
                    or len(digest) != 64
                    or len(Path(relative).parts) != 2
                    or Path(relative).is_absolute()
                    or ".." in Path(relative).parts
                    or Path(relative).name != "config.json"
                ):
                    raise ValueError("invalid frozen resource manifest entry")
                resource = root.joinpath(*Path(relative).parts)
                if (
                    not resource.is_file()
                    or hashlib.sha256(resource.read_bytes()).hexdigest() != digest
                ):
                    raise ValueError(f"altered frozen game definition: {relative}")
            discovered = {
                f"{entry.name}/config.json"
                for entry in root.iterdir()
                if entry.is_dir() and entry.joinpath("config.json").is_file()
            }
            if discovered != set(hashes):
                raise ValueError("frozen game resource catalog does not match manifest")
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise FileNotFoundError("invalid frozen game-resource integrity manifest") from error
    return root
