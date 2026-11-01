"""Find one trusted bundled game-data directory in every installation mode."""

from __future__ import annotations

import hashlib
import json
from importlib.util import find_spec
from pathlib import Path
import re
import sys


def bundled_games_root() -> Path:
    """Find bundled inert JSON files in source, installed or frozen applications.

    No user-writable or working-directory fallback can replace game rules.
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if not isinstance(base, str):
            raise FileNotFoundError("frozen application has no resource base")
        root: Path = Path(base) / "data"
    else:
        spec = find_spec("data")
        locations = () if spec is None else (spec.submodule_search_locations or ())
        candidates = {Path(location).resolve() for location in locations if Path(location).is_dir()}
        if len(candidates) != 1:
            raise FileNotFoundError("expected one installed data resource directory")
        root = next(iter(candidates))
    if not root.is_dir():
        raise FileNotFoundError("bundled game data directory is missing")
    if getattr(sys, "frozen", False):
        try:
            manifest = json.loads(root.joinpath("manifest.json").read_text(encoding="utf-8"))
            hashes = manifest["files"]
            if manifest["version"] != 1 or not isinstance(hashes, dict) or not hashes:
                raise ValueError("unsupported frozen resource manifest")
            for relative, digest in hashes.items():
                if (
                    not isinstance(relative, str)
                    or re.fullmatch(r"[a-z][a-z0-9_]{0,63}\\.json", relative) is None
                    or relative == "manifest.json"
                    or not isinstance(digest, str)
                    or re.fullmatch(r"[a-f0-9]{64}", digest) is None
                ):
                    raise ValueError("invalid frozen resource manifest entry")
                resource = root / relative
                if not resource.is_file() or hashlib.sha256(resource.read_bytes()).hexdigest() != digest:
                    raise ValueError(f"altered frozen game definition: {relative}")
            discovered = {
                entry.name
                for entry in root.iterdir()
                if entry.is_file() and entry.suffix == ".json" and entry.name != "manifest.json"
            }
            if discovered != set(hashes):
                raise ValueError("frozen game resource catalog does not match manifest")
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise FileNotFoundError("invalid frozen game-resource integrity manifest") from error
    return root
