import json
from pathlib import Path
from unittest.mock import patch
import pytest
from model.user import UserManager
from model.manager import GameManager
from model.move import Akce, Tah


def users(tmp_path):
    u = UserManager(tmp_path)
    u.vytvor_uzivatele(" Alice ", "Alice")
    u.vytvor_uzivatele("BOB", "Bob")
    return u


def test_normalization_and_reload(tmp_path):
    u = users(tmp_path)
    assert sorted(u.uzivatele) == ["alice", "bob"]
    with pytest.raises(ValueError):
        u.vytvor_uzivatele("ALICE", "Duplicate")
    assert UserManager(tmp_path).uzivatele["alice"].jmeno == "Alice"


def test_unique_chronological_match_files_and_resign(tmp_path):
    u = users(tmp_path)
    g = GameManager(u, "alice", "bob")
    m = next(m for m in g.mozne_tahy((6, 4)) if m.kam == (4, 4))
    g.proved_akci(Akce.move(m))
    g.proved_akci(Akce.resign())
    raw = json.loads(g.logger.path.read_text())
    assert raw["schema_version"] == 1 and raw["match_id"] == g.logger.match_id
    assert [x["index"] for x in raw["events"]] == [1, 2]
    assert raw["result"] == {"reason": "resignation", "winner": "alice"}
    second = g.reset()
    assert second.logger.match_id != g.logger.match_id
    assert g.logger.path.exists() and second.logger.path.exists()


def test_profiles_write_failure_and_retry_independent_from_history(tmp_path):
    u = users(tmp_path)
    g = GameManager(u, "alice", "bob")
    original = u.path.read_bytes()

    def failure(path, data):
        if Path(path) == u.path:
            raise OSError("simulated disk full")
        from model.user import atomic_json as real

        real(path, data)

    with patch("model.user.atomic_json", side_effect=OSError("disk full")):
        u.pridej_xp("alice", 10)
        assert not u.uloz_uzivatele()
        assert u.dirty and u.save_error
        assert u.path.read_bytes() == original
    assert u.uloz_uzivatele()
    assert UserManager(tmp_path).uzivatele["alice"].xp == 10
    assert not g.logger.save_error


def test_history_save_failure_and_retry(tmp_path):
    u = users(tmp_path)
    g = GameManager(u, "alice", "bob")
    previous = g.logger.path.read_bytes()
    g.logger.zaznamenej({"type": "resignation", "actor": "alice"}, "resignation", "black")
    with patch("model.logger.atomic_json", side_effect=OSError("read-only volume")):
        assert not g.logger.uloz_historii()
        assert g.logger.path.read_bytes() == previous
    assert g.logger.dirty and g.logger.save_error
    assert g.logger.uloz_historii()
    assert not g.logger.dirty and g.logger.save_error is None
    assert len(json.loads(g.logger.path.read_text())["events"]) == 1


def test_corrupt_profiles_preserved(tmp_path):
    path = tmp_path / "users.json"
    path.write_text("{not valid json")
    u = UserManager(tmp_path)
    assert u.damaged and u.save_error and u.uzivatele == {}
    u.vytvor_uzivatele("alice", "Alice")
    assert path.read_text() == "{not valid json"
    assert u.save_error


def test_corrupt_match_file_preserved(tmp_path):
    g = GameManager(users(tmp_path), "alice", "bob")
    g.logger.path.write_text("invalid historical data")
    assert not g.logger.uloz_historii()
    assert g.logger.path.read_text() == "invalid historical data"
    assert g.logger.damaged


def test_profile_and_history_save_status_independent_on_accepted_move(tmp_path):
    g = GameManager(users(tmp_path), "alice", "bob")
    g.users.uloz_uzivatele()
    move = next(m for m in g.mozne_tahy((6, 4)) if m.kam == (4, 4))
    with patch("model.logger.atomic_json", side_effect=OSError("history volume unavailable")):
        g.proved_akci(Akce.move(move))
    assert g.logger.save_error is not None
    assert g.users.save_error is None
    assert g.revision == 1
    assert g.logger.uloz_historii()


def test_damaged_profiles_can_be_moved_aside_then_retried(tmp_path):
    path = tmp_path / "users.json"
    path.write_text("{invalid", encoding="utf-8")
    u = UserManager(tmp_path)
    assert u.damaged
    u.vytvor_uzivatele("alice", "Alice")
    assert not u.uloz_uzivatele()
    broken = tmp_path / "users.original.invalid"
    path.rename(broken)
    assert u.uloz_uzivatele()
    assert not u.damaged and not u.dirty and u.save_error is None
    assert broken.read_text(encoding="utf-8") == "{invalid"
    assert UserManager(tmp_path).uzivatele["alice"].jmeno == "Alice"


def test_repaired_profile_file_merges_distinct_users_without_dropping_live_state(tmp_path):
    path = tmp_path / "users.json"
    path.write_text("corrupt", encoding="utf-8")
    u = UserManager(tmp_path)
    u.vytvor_uzivatele("alice", "Alice")
    u.pridej_xp("alice", 25)
    path.write_text(
        json.dumps({
            "schema_version": 1,
            "users": {"bob": {"username": "bob", "display_name": "Bob", "xp": 40}},
        }),
        encoding="utf-8",
    )
    assert u.uloz_uzivatele()
    restored = UserManager(tmp_path).uzivatele
    assert restored["alice"].xp == 25 and restored["bob"].xp == 40
    assert not u.damaged and not u.dirty


def test_repaired_profile_conflict_never_silently_overwrites_disk(tmp_path):
    path = tmp_path / "users.json"
    path.write_text("invalid", encoding="utf-8")
    u = UserManager(tmp_path)
    u.vytvor_uzivatele("alice", "Memory Alice")
    saved = json.dumps({
        "schema_version": 1,
        "users": {"alice": {
            "username": "alice", "display_name": "Disk Alice", "xp": 80,
        }},
    })
    path.write_text(saved, encoding="utf-8")
    assert not u.uloz_uzivatele()
    assert path.read_text(encoding="utf-8") == saved
    assert u.damaged and "conflicts" in u.save_error


def test_damaged_match_file_can_be_moved_aside_then_retried(tmp_path):
    g = GameManager(users(tmp_path), "alice", "bob")
    g.logger.path.write_text("broken", encoding="utf-8")
    assert not g.logger.uloz_historii() and g.logger.damaged
    backup = g.logger.path.with_suffix(".invalid")
    g.logger.path.rename(backup)
    move = next(m for m in g.mozne_tahy((6, 4)) if m.kam == (4, 4))
    g.proved_akci(Akce.move(move))
    assert backup.read_text(encoding="utf-8") == "broken"
    assert g.logger.path.is_file()
    assert not g.logger.damaged and not g.logger.dirty
    assert len(json.loads(g.logger.path.read_text(encoding="utf-8"))["events"]) == 1


def test_repaired_match_file_retries_only_when_history_is_consistent(tmp_path):
    g = GameManager(users(tmp_path), "alice", "bob")
    original = json.loads(g.logger.path.read_text(encoding="utf-8"))
    g.logger.path.write_text("broken", encoding="utf-8")
    assert not g.logger.uloz_historii()
    # Repair with the original, valid state; the store can resume normal saving.
    g.logger.path.write_text(json.dumps(original), encoding="utf-8")
    move = next(m for m in g.mozne_tahy((6, 4)) if m.kam == (4, 4))
    g.proved_akci(Akce.move(move))
    assert not g.logger.damaged
    valid = json.loads(g.logger.path.read_text(encoding="utf-8"))
    assert len(valid["events"]) == 1

    # Detect subsequent foreign edits rather than overwriting a different history.
    conflict = dict(valid)
    conflict["events"] = [{"index": 1, "type": "move", "actor": "mallory"}]
    altered = json.dumps(conflict)
    g.logger.path.write_text(altered, encoding="utf-8")
    assert not g.logger.uloz_historii()
    assert g.logger.damaged and "conflicts" in g.logger.save_error
    assert g.logger.path.read_text(encoding="utf-8") == altered
