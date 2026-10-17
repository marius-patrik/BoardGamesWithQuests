"""Consumer behavior and executed traversal evidence for compiled rule programs."""

from collections import Counter
from contextlib import contextmanager
import json
from pathlib import Path
import sys

import pytest

from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move

FIXTURE = Path(__file__).parent / "fixtures/chess_budget_reproducer.json"


@contextmanager
def observed_traversals():
    """Observe executed validation/config-copy calls without replacing behavior."""
    counts = Counter()

    def observe(frame, event, argument):
        if event != "call":
            return
        name = frame.f_code.co_name
        if name in {"validate_hooks", "condition"}:
            counts[name] += 1
        if name in {"thaw_json", "freeze_json", "_json_work"}:
            value = frame.f_locals.get("value")
            if hasattr(value, "keys") and {"schema_version", "pieces", "rules"} <= value.keys():
                counts["config_" + name] += 1

    prior = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield counts
    finally:
        sys.setprofile(prior)


def game(placement=None, *, targets=None):
    """Use the complete large definition with optional consumer-authored placement."""
    data = json.loads(FIXTURE.read_text())
    if placement is not None:
        data["board"]["starting_pieces"] = [
            {"piece": kind, "color": "white" if side == 1 else "black", "squares": [square]}
            for kind, side, square in placement
        ]
    if targets:
        data["initial_state"]["temporary_targets"].update(targets)
    return GameManager(validate_definition(data), "work", ("white", "black"), 0)


def test_legal_opening_and_move_do_not_recompile_or_copy_config_per_candidate():
    manager = game()
    with observed_traversals() as preview:
        assert len(manager.get_valid_moves()) == 20
    assert preview["validate_hooks"] == 0
    assert preview["config_thaw_json"] == preview["config_freeze_json"] == 0
    with observed_traversals() as action:
        event = manager.submit("white", 0, "first", Move((6, 4), (4, 4)), 1)
    assert action["validate_hooks"] == 0
    # Only publication serializes/freezes pinned configuration. Candidate count
    # does not multiply configuration traversals or static schema validation.
    assert action["config_thaw_json"] == action["config_freeze_json"] == 1
    assert event["revision"] == 1
    snapshot = manager.get_state()
    assert snapshot["temporary_targets"]["en_passant"] == [5, 4]
    assert GameManager.from_snapshot(snapshot).get_state() == snapshot
    snapshot["config"]["rules"].clear()
    assert manager.get_state()["config"]["rules"]


@pytest.mark.parametrize("wing,rook,end,rook_end", [("short", 7, 6, 5), ("long", 0, 2, 3)])
def test_full_program_castling_projects_auxiliary_piece_and_replays(wing, rook, end, rook_end):
    manager = game([("king", 1, [7, 4]), ("rook", 1, [7, rook]), ("king", -1, [0, 4])])
    intent = Move((7, 4), (7, end))
    assert intent in manager.get_valid_moves()
    event = manager.submit("white", 0, "castle-" + wing, intent, 1)
    snapshot = manager.get_state()
    assert any(p["kind"] == "rook" and p["square"] == [7, rook_end] for p in snapshot["board"])
    assert snapshot["special_rights"]["white_short"] is False
    assert snapshot["special_rights"]["white_long"] is False
    restored = GameManager.from_snapshot(snapshot)
    assert restored.get_state() == snapshot
    assert restored.submit("white", 0, "castle-" + wing, intent, 999) == event


@pytest.mark.parametrize("pinned", [False, True])
def test_full_program_en_passant_preserves_projection_safety_and_rollback(pinned):
    pieces = [
        ("king", 1, [3, 0] if pinned else [7, 0]),
        ("king", -1, [0, 0]),
        ("pawn", 1, [3, 2]),
        ("pawn", -1, [3, 3]),
    ]
    if pinned:
        pieces.append(("rook", -1, [3, 7]))
    manager = game(pieces, targets={"en_passant": [2, 3]})
    intent = Move((3, 2), (2, 3))
    before = manager.get_state()
    if pinned:
        assert intent not in manager.get_valid_moves()
        with pytest.raises(TransitionError):
            manager.submit("white", 0, "passing", intent, 1)
        assert manager.get_state() == before
    else:
        assert intent in manager.get_valid_moves()
        event = manager.submit("white", 0, "passing", intent, 1)
        assert event["captured"] == [[3, 3]]
        snapshot = manager.get_state()
        assert all(p["square"] != [3, 3] for p in snapshot["board"])
        assert snapshot["temporary_targets"]["en_passant"] is None
        assert GameManager.from_snapshot(snapshot).get_state() == snapshot
