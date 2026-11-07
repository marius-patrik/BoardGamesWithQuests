"""Enforce the canonical flat, inert game-data layout and frozen integrity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

from model.games import available_games
from model.resources import bundled_games_root

ROOT = Path(__file__).resolve().parents[2]


def test_flat_data_and_single_main_entrypoint() -> None:
    assert available_games() == ["chess", "checkers"]
    assert sorted(path.name for path in (ROOT / "data").iterdir()) == [
        "checkers.json",
        "chess.json",
    ]
    assert not (ROOT / "games").exists()
    assert not (ROOT / "src/boardgameswithquests.py").exists()
    assert (ROOT / "src/main.py").is_file()
    for name in ("chess", "checkers"):
        assert (bundled_games_root() / f"{name}.json").read_bytes() == (
            ROOT / "data" / f"{name}.json"
        ).read_bytes()


def test_frozen_manifest_and_tamper_rejection(tmp_path: Path, monkeypatch) -> None:
    data = tmp_path / "data"
    data.mkdir()
    hashes = {}
    for name in ("chess", "checkers"):
        filename = f"{name}.json"
        payload = (ROOT / "data" / filename).read_bytes()
        (data / filename).write_bytes(payload)
        hashes[filename] = hashlib.sha256(payload).hexdigest()
    (data / "manifest.json").write_text(
        json.dumps({"version": 1, "files": hashes}), encoding="utf-8"
    )
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert bundled_games_root() == data
    (data / "checkers.json").write_text("tampered", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="integrity manifest"):
        bundled_games_root()


def test_frozen_manifest_rejects_path_escape_and_extra_json(tmp_path: Path, monkeypatch) -> None:
    data = tmp_path / "data"
    data.mkdir()
    payload = (ROOT / "data/chess.json").read_bytes()
    (data / "chess.json").write_bytes(payload)
    (data / "manifest.json").write_text(
        json.dumps({"version": 1, "files": {"../chess.json": hashlib.sha256(payload).hexdigest()}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    with pytest.raises(FileNotFoundError, match="integrity manifest"):
        bundled_games_root()
    (data / "manifest.json").write_text(
        json.dumps({"version": 1, "files": {"chess.json": hashlib.sha256(payload).hexdigest()}}),
        encoding="utf-8",
    )
    (data / "unexpected.json").write_text("extra", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="integrity manifest"):
        bundled_games_root()
