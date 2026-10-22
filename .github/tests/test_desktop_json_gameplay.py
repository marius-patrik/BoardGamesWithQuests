"""Player-observable local session transaction acceptance through its public API."""

from __future__ import annotations

import pytest

from model.game.manager import TransitionError
from model.game.session import DesktopSession


def chess_pawn_action(session):
    return {
        "type": "move",
        "move": next(
            move
            for move in session.legal_actions()
            if move["start"] == [6, 4] and move["hops"] == [[5, 4]]
        ),
    }


def square(snapshot, coordinate):
    return next((entry for entry in snapshot["board"] if entry["square"] == coordinate), None)


def test_desktop_gameplay_actions_retry_stale_recovery_and_reset():
    session = DesktopSession("chess")
    opening = session.snapshot()
    assert square(opening, [6, 4])["kind"] == "pawn"
    assert square(opening, [5, 4]) is None
    action = chess_pawn_action(session)
    chosen = session.submit("white", 0, action, action_id="opening-e4")
    updated = chosen["state"]
    assert updated["revision"] == 1
    assert square(updated, [6, 4]) is None
    assert square(updated, [5, 4])["kind"] == "pawn"
    assert updated["active_side"] == -1
    assert len(updated["events"]) == 1
    assert session.submit("white", 0, action, action_id="opening-e4")["event"] == chosen["event"]
    assert session.snapshot() == updated
    with pytest.raises(TransitionError):
        session.submit("white", 0, action, action_id="different-at-stale")
    assert session.snapshot() == updated
    with pytest.raises(TransitionError):
        session.submit("white", 0, {"type": "resign"}, action_id="opening-e4")
    assert session.snapshot() == updated
    restored = DesktopSession.recover(updated)
    assert restored.snapshot() == updated
    assert restored.legal_actions() == session.legal_actions()
    new = session.reset("checkers")
    assert new["revision"] == 0 and len(new["board"]) == 24
    assert session.game == "checkers"
    assert restored.snapshot() == updated


def test_illegal_action_does_not_advance_session_or_clock():
    session = DesktopSession("chess")
    baseline = session.snapshot()
    attempted = {
        "type": "move",
        "move": {"start": [6, 4], "hops": [[3, 4]], "promotion": None},
    }
    with pytest.raises(TransitionError):
        session.submit("white", 0, attempted, action_id="illegal-jump")
    assert session.snapshot() == baseline


def test_wrong_actor_does_not_mutate_game_state():
    session = DesktopSession("chess")
    baseline = session.snapshot()
    with pytest.raises(TransitionError):
        session.submit("black", 0, chess_pawn_action(session), action_id="wrong-turn")
    assert session.snapshot() == baseline
