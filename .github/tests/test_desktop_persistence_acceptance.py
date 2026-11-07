"""Source-level process-restart and hostile local-storage acceptance for issue #439.

These tests use the shipped configurations and real DesktopSession transitions.
Native frozen-app restarts on four platforms remain a separate #443 gate.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from model.manager import MAX_SNAPSHOT_BYTES
from model.persistence import SessionFileError, load_session, save_session
from model.preferences import (
    DEFAULTS,
    PreferencesError,
    load_preferences,
    preferences_directory,
    save_preferences,
)
from model.session import DesktopSession

ROOT = Path(__file__).resolve().parents[2]


def _process(script: str, *args: object, env: dict[str, str] | None = None) -> dict:
    child_env = os.environ.copy()
    child_env["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(ROOT / "src"), child_env.get("PYTHONPATH", "")))
    )
    if env is not None:
        child_env.update(env)
    result = subprocess.run(
        [sys.executable, "-c", script, *(str(arg) for arg in args)],
        cwd=ROOT,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (
        f"process {result.pid if hasattr(result, 'pid') else 'child'} exited "
        f"{result.returncode}: {result.stderr}"
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    ("game", "opening", "response", "starting_count"),
    [
        ("chess", ((6, 4), (4, 4)), ((1, 4), (3, 4)), 32),
        ("checkers", ((2, 3), (3, 2)), ((5, 0), (4, 1)), 24),
    ],
)
def test_save_exit_reopen_and_continue_in_another_process(
    tmp_path, game, opening, response, starting_count
):
    path = tmp_path / "recovered.json"
    before = _process(
        """
import json, os, sys
from model.persistence import save_session
from model.session import DesktopSession

path, game = sys.argv[1:3]
start, end = json.loads(sys.argv[3]), json.loads(sys.argv[4])
session = DesktopSession(game)
initial = session.snapshot()
action = next(m for m in session.legal_actions()
              if m["start"] == start and m["hops"][-1] == end)
actor = initial["participants"][str(initial["active_side"])]
session.submit(actor, 0, {"type": "move", "move": action}, action_id="first-turn")
save_session(session, path)
print(json.dumps({"pid": os.getpid(), "initial_pieces": len(initial["board"]),
                  "snapshot": session.snapshot()}))
""",
        path,
        game,
        json.dumps(opening[0]),
        json.dumps(opening[1]),
    )
    assert before["initial_pieces"] == starting_count
    assert before["snapshot"]["revision"] == 1
    assert len(before["snapshot"]["events"]) == 1
    assert json.loads(path.read_text(encoding="utf-8")) == before["snapshot"]

    after = _process(
        """
import json, os, sys
from model.persistence import load_session

session = load_session(sys.argv[1])
recovered = session.snapshot()
start, end = json.loads(sys.argv[2]), json.loads(sys.argv[3])
action = next(m for m in session.legal_actions()
              if m["start"] == start and m["hops"][-1] == end)
actor = recovered["participants"][str(recovered["active_side"])]
session.submit(actor, recovered["revision"], {"type": "move", "move": action},
               action_id="second-turn")
print(json.dumps({"pid": os.getpid(), "game": session.game,
                  "recovered": recovered, "continued": session.snapshot()}))
""",
        path,
        json.dumps(response[0]),
        json.dumps(response[1]),
    )
    assert before["pid"] != after["pid"]
    assert after["game"] == game
    assert after["recovered"] == before["snapshot"]
    assert after["continued"]["revision"] == 2
    assert len(after["continued"]["events"]) == 2
    assert after["continued"]["active_side"] == -before["snapshot"]["active_side"]


def test_settings_survive_an_actual_process_restart_and_reject_corruption(tmp_path):
    isolated = {
        "HOME": str(tmp_path),
        "USERPROFILE": str(tmp_path),
        "APPDATA": str(tmp_path / "appdata"),
        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
    }
    written = _process(
        """
import json, os
from model.preferences import preferences_directory, save_preferences
settings = save_preferences({"board_size": 64, "show_coordinates": False})
print(json.dumps({"pid": os.getpid(), "path": str(preferences_directory()),
                  "settings": settings}))
""",
        env=isolated,
    )
    recovered = _process(
        """
import json, os
from model.preferences import load_preferences
print(json.dumps({"pid": os.getpid(), "settings": load_preferences()}))
""",
        env=isolated,
    )
    assert written["pid"] != recovered["pid"]
    assert (
        recovered["settings"]
        == written["settings"]
        == {
            "board_size": 64,
            "show_coordinates": False,
        }
    )
    saved = Path(written["path"]) / "preferences.json"
    assert json.loads(saved.read_text(encoding="utf-8")) == recovered["settings"]
    saved.write_text('{"board_size": 50, "board_size": 64, "show_coordinates": false}')
    with pytest.raises(PreferencesError, match="duplicate"):
        load_preferences(Path(written["path"]))


@pytest.mark.parametrize(
    "invalid",
    [
        b'{"board_size":56,"board_size":72,"show_coordinates":true}',
        b'{"board_size":55,"show_coordinates":true,"rules":{"python":"exec"}}',
        b'{"board_size":NaN,"show_coordinates":true}',
        b'{"board_size":true,"show_coordinates":true}',
        b'{"board_size":56,"show_coordinates":"true"}',
        b'{"board_size":56,',
        b"[]",
        b"\xff",
        b" " * 4097,
    ],
)
def test_reject_hostile_settings_without_overwriting_existing_values(tmp_path, invalid):
    directory = tmp_path / "settings"
    assert load_preferences(directory) == DEFAULTS
    save_preferences({"board_size": 68, "show_coordinates": False}, directory)
    path = directory / "preferences.json"
    path.write_bytes(invalid)
    with pytest.raises(PreferencesError):
        load_preferences(directory)
    assert path.read_bytes() == invalid


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate",
        "invalid_utf8",
        "oversized",
        "broken_json",
        "non_object",
        "nonfinite",
        "invalid_schema",
        "tampered_board",
        "tampered_history",
        "tampered_clock",
    ],
)
def test_invalid_save_is_rejected_without_mutating_an_active_game(tmp_path, corruption):
    current = DesktopSession("chess")
    initial = current.snapshot()
    opening = next(
        m for m in current.legal_actions() if m["start"] == [6, 4] and m["hops"][-1] == [4, 4]
    )
    current.submit("white", 0, {"type": "move", "move": opening})
    before = current.snapshot()
    path = tmp_path / "import.json"
    payload = json.loads(json.dumps(before))
    if corruption == "duplicate":
        raw = b'{"version":1,"version":1}'
    elif corruption == "invalid_utf8":
        raw = b"\xff"
    elif corruption == "oversized":
        raw = b" " * (MAX_SNAPSHOT_BYTES + 1)
    elif corruption == "broken_json":
        raw = b'{"version":'
    elif corruption == "non_object":
        raw = b"[]"
    elif corruption == "nonfinite":
        raw = b'{"revision":NaN}'
    else:
        if corruption == "invalid_schema":
            payload["version"] = 999
        elif corruption == "tampered_board":
            payload["board"].clear()
        elif corruption == "tampered_history":
            payload["events"][0]["actor"] = "spoofed"
        else:
            payload["clocks"]["remaining_ms"]["1"] = -1
        raw = json.dumps(payload).encode("utf-8")
    path.write_bytes(raw)
    with pytest.raises(SessionFileError):
        load_session(path)
    assert current.snapshot() == before
    assert current.snapshot()["revision"] == 1
    assert initial["board"] != before["board"]


def test_atomic_overwrite_and_failed_save_preserve_live_state_and_prior_file(tmp_path):
    session = DesktopSession("chess")
    path = tmp_path / "game.json"
    save_session(session, path)
    original = path.read_bytes()
    assert load_session(path).snapshot() == session.snapshot()
    move = next(
        m for m in session.legal_actions() if m["start"] == [6, 4] and m["hops"][-1] == [4, 4]
    )
    session.submit("white", 0, {"type": "move", "move": move})
    state = session.snapshot()
    outside = tmp_path / "outside.json"
    outside.write_bytes(original)
    symlink = tmp_path / "linked.json"
    try:
        symlink.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform/account")
    with pytest.raises(SessionFileError):
        save_session(session, symlink)
    with pytest.raises(SessionFileError):
        load_session(symlink)
    assert outside.read_bytes() == original
    with pytest.raises(SessionFileError):
        save_session(session, tmp_path / "missing-parent" / "game.json")
    assert path.read_bytes() == original
    assert session.snapshot() == state
    assert not list(tmp_path.glob(".bgwq-*"))
    save_session(session, path)
    assert path.read_bytes() != original
    assert load_session(path).snapshot() == state
    assert not list(tmp_path.glob(".bgwq-*"))


def test_symlinked_parent_and_traversal_are_rejected_for_both_data_types(tmp_path):
    trusted = tmp_path / "real"
    trusted.mkdir()
    game = DesktopSession("checkers")
    save_session(game, trusted / "game.json")
    save_preferences(DEFAULTS, trusted)
    link = tmp_path / "alias"
    try:
        link.symlink_to(trusted, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks unavailable on this platform/account")
    with pytest.raises(SessionFileError):
        load_session(link / "game.json")
    with pytest.raises(SessionFileError):
        save_session(game, link / "another.json")
    with pytest.raises(PreferencesError):
        load_preferences(link)
    with pytest.raises(PreferencesError):
        save_preferences(DEFAULTS, link)
    with pytest.raises(SessionFileError):
        save_session(game, trusted / ".." / "another.json")
    with pytest.raises(PreferencesError):
        save_preferences(DEFAULTS, trusted / ".." / "other")
    assert load_session(trusted / "game.json").snapshot() == game.snapshot()
    assert load_preferences(trusted) == DEFAULTS


def test_reject_nonregular_saved_game_and_preferences_files(tmp_path):
    directory = tmp_path / "settings"
    directory.mkdir()
    (directory / "preferences.json").mkdir()
    with pytest.raises(PreferencesError):
        load_preferences(directory)
    with pytest.raises(PreferencesError):
        save_preferences(DEFAULTS, directory)
    game_directory = tmp_path / "game.json"
    game_directory.mkdir()
    with pytest.raises(SessionFileError):
        load_session(game_directory)
    with pytest.raises(SessionFileError):
        save_session(DesktopSession("chess"), game_directory)


def test_read_only_targets_and_unwritable_directories_preserve_existing_data(tmp_path):
    game = DesktopSession("chess")
    game_path = tmp_path / "game.json"
    save_session(game, game_path)
    game_bytes = game_path.read_bytes()
    settings_dir = tmp_path / "settings"
    save_preferences(DEFAULTS, settings_dir)
    settings_path = settings_dir / "preferences.json"
    settings_bytes = settings_path.read_bytes()

    try:
        game_path.chmod(0o444)
        settings_path.chmod(0o444)
        with pytest.raises(SessionFileError, match="read-only"):
            save_session(game, game_path)
        with pytest.raises(PreferencesError, match="read-only"):
            save_preferences({"board_size": 80, "show_coordinates": False}, settings_dir)
        assert game_path.read_bytes() == game_bytes
        assert settings_path.read_bytes() == settings_bytes
    finally:
        game_path.chmod(0o644)
        settings_path.chmod(0o644)

    if os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() == 0):
        pytest.skip("directory mode denial requires an unprivileged POSIX account")
    try:
        settings_dir.chmod(0o555)
        with pytest.raises(OSError):
            save_preferences(DEFAULTS, settings_dir)
        assert settings_path.read_bytes() == settings_bytes
    finally:
        settings_dir.chmod(0o755)
    assert not list(settings_dir.glob(".preferences-*"))


def test_interrupted_replacement_cleans_temp_and_preserves_old_files(tmp_path, monkeypatch):
    """Injected rename failure: real disk writes and fsync still run before the fault."""
    import model.persistence as persistence
    import model.preferences as preferences

    game = DesktopSession("checkers")
    filename = tmp_path / "game.json"
    save_session(game, filename)
    saved_game = filename.read_bytes()
    directory = tmp_path / "settings"
    save_preferences(DEFAULTS, directory)
    pref = directory / "preferences.json"
    saved_pref = pref.read_bytes()

    def interrupted(*args, **kwargs):
        raise PermissionError("injected rename interruption")

    monkeypatch.setattr(os, "replace", interrupted)
    with pytest.raises(PermissionError, match="injected"):
        persistence.save_session(game, filename)
    with pytest.raises(PermissionError, match="injected"):
        preferences.save_preferences({"board_size": 72, "show_coordinates": False}, directory)
    assert filename.read_bytes() == saved_game
    assert pref.read_bytes() == saved_pref
    assert not list(tmp_path.glob(".bgwq-*"))
    assert not list(directory.glob(".preferences-*"))


def test_concurrent_target_change_causes_non_destructive_save_rejection(tmp_path, monkeypatch):
    """Change the real target after the initial check, before the final replace."""
    import model.persistence as persistence

    session = DesktopSession("chess")
    path = tmp_path / "game.json"
    save_session(session, path)
    concurrent_bytes = b"concurrent writer"
    original_mkstemp = persistence.tempfile.mkstemp

    def change_target(*args, **kwargs):
        result = original_mkstemp(*args, **kwargs)
        path.write_bytes(concurrent_bytes)
        return result

    monkeypatch.setattr(persistence.tempfile, "mkstemp", change_target)
    with pytest.raises(SessionFileError, match="changed"):
        save_session(session, path)
    assert path.read_bytes() == concurrent_bytes
    assert not list(tmp_path.glob(".bgwq-*"))
