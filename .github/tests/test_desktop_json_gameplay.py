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


def perform(session, source, target, promotion=None):
    """Play the actual exact legal intent exposed to the current participant."""
    snapshot = session.snapshot()
    actor = snapshot["participants"][str(snapshot["active_side"])]
    matching = [
        move
        for move in session.legal_actions()
        if move["start"] == list(source)
        and move["hops"][-1] == list(target)
        and move["promotion"] == promotion
    ]
    assert len(matching) == 1, {"from": source, "to": target, "available": session.legal_actions()}
    return session.submit(
        actor,
        snapshot["revision"],
        {"type": "move", "move": matching[0]},
        action_id=f"ply-{snapshot['revision'] + 1}",
    )


def test_scholars_mate_from_normal_chess_start_using_full_rulebook():
    """Seven actual player turns must end at an authoritative checkmate result."""
    session = DesktopSession("chess")
    script = [
        ((6, 4), (4, 4)),  # e4
        ((1, 4), (3, 4)),  # ... e5
        ((7, 3), (3, 7)),  # Qh5
        ((0, 1), (2, 2)),  # ... Nc6
        ((7, 5), (4, 2)),  # Bc4
        ((0, 6), (2, 5)),  # ... Nf6
        ((3, 7), (1, 5)),  # Qxf7#
    ]
    for start, end in script:
        result = perform(session, start, end)
    state = result["state"]
    assert state["revision"] == len(script)
    assert len(state["events"]) == len(script)
    assert state["outcome"] is not None
    assert state["outcome"]["kind"] == "win"
    assert state["outcome"]["winner"] == "white"
    with pytest.raises(TransitionError):
        session.submit("black", state["revision"], {"type": "resign"})
    assert DesktopSession.recover(state).snapshot() == state


def test_english_draughts_forced_capture_updates_authoritative_history():
    """A real opening must produce a mandatory short capture and deterministic replay."""
    session = DesktopSession("checkers")
    assert len(session.snapshot()["board"]) == 24
    perform(session, (5, 0), (4, 1))
    perform(session, (2, 3), (3, 2))
    available = session.legal_actions()
    capture = [move for move in available if move["start"] == [4, 1] and move["hops"] == [[2, 3]]]
    assert capture, available
    state = perform(session, (4, 1), (2, 3))["state"]
    assert state["revision"] == 3
    assert len(state["captured"]) == 1
    assert state["captured"][0]["side"] == -1
    assert square(state, [3, 2]) is None
    assert square(state, [2, 3])["side"] == 1
    assert DesktopSession.recover(state).snapshot() == state


def test_reset_recovers_original_position_without_leaking_previous_moves():
    session = DesktopSession("chess")
    before = session.snapshot()
    perform(session, (6, 4), (4, 4))
    reset = session.reset()
    assert reset["revision"] == 0
    assert reset["game_id"] != before["game_id"]
    assert reset["board"] == before["board"]
    assert reset["events"] == []
