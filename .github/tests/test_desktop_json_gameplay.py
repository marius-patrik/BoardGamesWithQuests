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
    # Official English draughts opens with Black.
    assert session.snapshot()["active_side"] == -1
    perform(session, (2, 3), (3, 2))
    perform(session, (5, 0), (4, 1))
    available = session.legal_actions()
    capture = [move for move in available if move["start"] == [3, 2] and move["hops"] == [[5, 0]]]
    assert capture, available
    state = perform(session, (3, 2), (5, 0))["state"]
    assert state["revision"] == 3
    assert len(state["captured"]) == 1
    assert state["captured"][0]["side"] == 1
    assert square(state, [4, 1]) is None
    assert square(state, [5, 0])["side"] == -1
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


def test_quest_rewards_are_awarded_exactly_once_through_gameplay_and_replay():
    session = DesktopSession("chess")
    assert session.snapshot()["quest_scores"] == {"white": 0, "black": 0}
    first = perform(session, (6, 4), (4, 4))["state"]
    assert first["quest_progress"]["white"]["first-move"]["completed"]
    assert first["quest_scores"] == {"white": 5, "black": 0}
    second = perform(session, (1, 4), (3, 4))["state"]
    assert second["quest_scores"] == {"white": 5, "black": 5}
    perform(session, (7, 6), (5, 5))
    perform(session, (0, 1), (2, 2))
    fifth = perform(session, (5, 5), (3, 4))["state"]
    assert fifth["quest_progress"]["white"]["first-capture"]["completed"]
    assert fifth["quest_scores"]["white"] == 15
    assert DesktopSession.recover(fifth).snapshot() == fifth


def test_castling_moves_the_rook_and_king_atomically():
    session = DesktopSession("chess")
    for start, end in (
        ((7, 6), (5, 5)),  # Nf3
        ((0, 6), (2, 5)),  # ... Nf6
        ((6, 6), (5, 6)),  # g3
        ((1, 6), (2, 6)),  # ... g6
        ((7, 5), (6, 6)),  # Bg2
        ((0, 5), (1, 6)),  # ... Bg7
    ):
        perform(session, start, end)
    before = session.snapshot()
    assert any(m["start"] == [7, 4] and m["hops"][-1] == [7, 6] for m in session.legal_actions())
    after = perform(session, (7, 4), (7, 6))["state"]
    assert square(after, [7, 4]) is None
    assert square(after, [7, 6])["kind"] == "king"
    assert square(after, [7, 7]) is None
    assert square(after, [7, 5])["kind"] == "rook"
    assert after["revision"] == before["revision"] + 1
    assert DesktopSession.recover(after).snapshot() == after


def test_en_passant_removes_the_correct_opponent_pawn_and_replays():
    session = DesktopSession("chess")
    for start, end in (
        ((6, 4), (4, 4)),  # e4
        ((1, 0), (2, 0)),  # ... a6
        ((4, 4), (3, 4)),  # e5
        ((1, 3), (3, 3)),  # ... d5
    ):
        perform(session, start, end)
    before = session.snapshot()
    legal = session.legal_actions()
    assert any(m["start"] == [3, 4] and m["hops"][-1] == [2, 3] for m in legal)
    after = perform(session, (3, 4), (2, 3))["state"]
    assert square(after, [3, 3]) is None
    assert square(after, [2, 3])["kind"] == "pawn"
    assert len(after["captured"]) == len(before["captured"]) + 1
    assert DesktopSession.recover(after).snapshot() == after


def test_real_installation_check_executes_both_bundled_game_openings():
    import subprocess
    import sys

    completed = subprocess.run(
        [sys.executable, "-m", "chesswithquests", "--check"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert completed.returncode == 0, completed.stderr
    assert "accepted and replayed opening moves: 2" in completed.stdout


def test_fools_mate_and_opening_legal_counts_through_real_session():
    session = DesktopSession("chess")
    assert len(session.legal_actions()) == 20
    perform(session, (6, 5), (5, 5))  # f3
    assert len(session.legal_actions()) == 20
    perform(session, (1, 4), (3, 4))  # ... e5
    perform(session, (6, 6), (4, 6))  # g4
    state = perform(session, (0, 3), (4, 7))["state"]  # ... Qh4#
    assert state["outcome"]["kind"] == "win"
    assert state["outcome"]["winner"] == "black"
    assert not session.legal_actions()
    assert DesktopSession.recover(state).snapshot() == state


def test_english_draughts_initial_legal_count_and_forced_capture_precedence():
    session = DesktopSession("checkers")
    assert len(session.legal_actions()) == 7
    perform(session, (2, 3), (3, 2))
    perform(session, (5, 0), (4, 1))
    legal = session.legal_actions()
    assert legal
    assert all(move["hops"][-1] != [4, 3] for move in legal)
    assert all(move["start"] == [3, 2] and move["hops"] == [[5, 0]] for move in legal)



def test_english_draughts_resignation_is_visible_as_authoritative_terminal_result():
    session = DesktopSession("checkers")
    state = session.snapshot()
    result = session.submit(
        "black", state["revision"], {"type": "resign"},
        action_id="black-resigns",
    )["state"]
    assert result["outcome"]["kind"] == "win"
    assert result["outcome"]["winner"] == "white"
    assert result["outcome"]["cause"] == "resignation"
    assert not session.legal_actions()
    assert DesktopSession.recover(result).snapshot() == result


def test_english_draughts_clock_expiration_commits_and_replays_timeout(monkeypatch):
    from model.game.session import time

    session = DesktopSession("checkers")
    state = session.snapshot()
    expiration_ms = state["started_at_ms"] + 600_001
    monkeypatch.setattr(time, "time_ns", lambda: expiration_ms * 1_000_000)
    assert session.poll_timeout() is True
    expired = session.snapshot()
    assert expired["outcome"]["kind"] == "win"
    assert expired["outcome"]["winner"] == "white"
    assert expired["outcome"]["cause"] == "timeout"
    assert expired["clocks"]["remaining_ms"]["-1"] == 0
    assert session.poll_timeout() is False
    assert DesktopSession.recover(expired).snapshot() == expired
