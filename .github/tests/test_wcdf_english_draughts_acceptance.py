"""WCDF English Draughts behavioral references through the shipped JSON game.

Rules: WCDF 2025 Rules of Draughts, articles 1.11-1.21 and 1.29-1.32:
https://nccheckers.org/NCCA/WCDF%20Checker%20-%20Draughts%20-%20English%20Rules.htm

The existing 91-ply Tinsley-Long 1981 game is independently replayed through
DesktopSession by test_desktop_full_draughts.py; keep that test unchanged.
No alternate production move generator or modified/pruned JSON rules are used.
"""

from __future__ import annotations

from importlib import resources
import json

import pytest

from model.game.definition import validate_definition
from model.game.manager import GameManager, TransitionError
from model.game.move import Move
from model.game.session import DesktopSession


def reference_game(pieces, *, start=-1):
    """Create an authoritative game at a small explicitly specified WCDF position."""
    data = json.loads(resources.files("games").joinpath("checkers", "config.json").read_text())
    data["starting_side"] = start
    data["board"]["starting_pieces"] = [
        {
            "piece": kind,
            "color": "white" if side == 1 else "black",
            "squares": [list(square)],
        }
        for kind, side, square in pieces
    ]
    return GameManager(validate_definition(data), "wcdf-reference", ("white", "black"), 0)


def act(game, move, *, now=None):
    state = game.get_state()
    side = str(state["active_side"])
    return game.submit_action(
        state["participants"][side],
        state["revision"],
        f"wcdf-action-{state['revision'] + 1}",
        {"type": "move", "move": move.to_json()},
        state["revision"] + 1 if now is None else now,
    )


def claim(game, name, *, intended=None, action_id="wcdf-claim"):
    state = game.get_state()
    return game.submit_action(
        state["participants"][str(state["active_side"])],
        state["revision"],
        action_id,
        {
            "type": "claim_draw",
            "claim": name,
            "intended_move": intended.to_json() if intended else None,
        },
        state["revision"] + 1,
    )


def reject(game, intent, *, actor=None, action_id="wcdf-invalid"):
    state = game.get_state()
    with pytest.raises(TransitionError):
        game.submit_action(
            actor or state["participants"][str(state["active_side"])],
            state["revision"],
            action_id,
            intent,
            state["revision"] + 1,
        )
    assert game.get_state() == state


def piece(state, square):
    return next((p for p in state["board"] if p["square"] == list(square)), None)


def test_wcdfs_shipped_initial_setup_and_seven_black_opening_choices():
    session = DesktopSession("checkers")
    state = session.snapshot()
    assert state["active_side"] == -1  # WCDF 1.13: red/black moves first.
    assert state["revision"] == 0 and state["outcome"] is None
    assert len(state["board"]) == 24
    assert len([p for p in state["board"] if p["side"] == -1]) == 12
    assert len([p for p in state["board"] if p["side"] == 1]) == 12
    assert {p["kind"] for p in state["board"]} == {"man"}
    assert all(sum(p["square"]) % 2 == 1 for p in state["board"])
    assert len(session.legal_actions()) == 7
    assert {tuple(m["start"]) for m in session.legal_actions()} == {
        (2, 1),
        (2, 3),
        (2, 5),
        (2, 7),
    }
    assert state["config"]["pieces"]["man"]["capture_policy"]["flying"] is False
    assert state["config"]["pieces"]["king"]["capture_policy"]["flying"] is False


def test_men_advance_forward_only_and_cannot_capture_backwards():
    game = reference_game(
        [
            ("man", -1, (2, 3)),
            ("man", 1, (7, 0)),
        ]
    )
    assert set(game.get_valid_moves()) == {
        Move((2, 3), (3, 2)),
        Move((2, 3), (3, 4)),
    }
    reject(game, {"type": "move", "move": Move((2, 3), (1, 2)).to_json()})
    game = reference_game(
        [
            ("man", -1, (4, 3)),
            ("man", 1, (3, 2)),
            ("man", 1, (7, 0)),
        ]
    )
    # A diagonally backward enemy is not capturable by an uncrowned man.
    assert Move((4, 3), (2, 1)) not in game.get_valid_moves()


def test_king_moves_and_captures_one_step_or_one_jump_not_flying():
    game = reference_game(
        [
            ("king", -1, (2, 3)),
            ("man", 1, (7, 0)),
        ]
    )
    legal = set(game.get_valid_moves())
    assert {
        Move((2, 3), (1, 2)),
        Move((2, 3), (1, 4)),
        Move((2, 3), (3, 2)),
        Move((2, 3), (3, 4)),
    } == legal
    assert Move((2, 3), (4, 5)) not in legal
    game = reference_game(
        [
            ("king", -1, (2, 3)),
            ("man", 1, (1, 2)),
            ("man", 1, (7, 0)),
        ]
    )
    assert Move((2, 3), (0, 1)) in game.get_valid_moves()
    assert all(m.hops[0] == (0, 1) for m in game.get_valid_moves())


def test_compulsory_captures_allow_shorter_and_longer_alternatives():
    # WCDF 1.20: no maximum-capture rule; either full route is legal.
    game = reference_game(
        [
            ("man", -1, (2, 3)),
            ("man", 1, (3, 2)),
            ("man", 1, (3, 4)),
            ("man", 1, (5, 6)),
            ("man", 1, (7, 0)),
        ]
    )
    short = Move((2, 3), (4, 1))
    long = Move((2, 3), (6, 7), hops=((4, 5), (6, 7)))
    assert set(game.get_valid_moves()) == {short, long}
    reject(game, {"type": "move", "move": Move((2, 3), (4, 5)).to_json()})
    reject(game, {"type": "move", "move": Move((2, 3), (3, 2)).to_json()})
    result = act(game, long)
    assert {tuple(square) for square in result["captured"]} == {(3, 4), (5, 6)}
    after = game.get_state()
    assert piece(after, (6, 7))["kind"] == "man"
    assert piece(after, (3, 2)) is not None
    assert piece(after, (3, 4)) is None
    assert piece(after, (5, 6)) is None
    assert GameManager.from_snapshot(after).get_state() == after


def test_two_distinct_complete_capture_sequences_with_same_end_are_not_collapsed():
    game = reference_game(
        [
            ("man", -1, (2, 3)),
            ("man", 1, (3, 2)),
            ("man", 1, (5, 2)),
            ("man", 1, (3, 4)),
            ("man", 1, (5, 4)),
            ("man", 1, (7, 0)),
        ]
    )
    left = Move((2, 3), (6, 3), hops=((4, 1), (6, 3)))
    right = Move((2, 3), (6, 3), hops=((4, 5), (6, 3)))
    assert {left, right} == set(game.get_valid_moves())
    reject(game, {"type": "move", "move": Move((2, 3), (6, 3)).to_json()})
    result = act(game, left)
    assert {tuple(square) for square in result["captured"]} == {(3, 2), (5, 2)}
    assert piece(game.get_state(), (3, 4)) is not None
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_capture_removal_policy_matches_wcdf_and_replay_is_atomic():
    # WCDF 1.19: captured men are removed at the end of a whole sequence.
    # In short-jump geometry each landing has the start row's parity, while
    # jumped-square rows have the opposite parity: no already-captured square
    # can serve as a later landing. This is not an FMJD/flying-king rule.
    game = reference_game(
        [
            ("king", -1, (2, 3)),
            ("man", 1, (3, 4)),
            ("man", 1, (5, 6)),
            ("man", 1, (7, 0)),
        ]
    )
    assert all(
        game.get_state()["config"]["pieces"][kind]["capture_policy"]["deferred_removal"]
        for kind in ("man", "king")
    )
    expected = Move((2, 3), (6, 7), hops=((4, 5), (6, 7)))
    assert set(game.get_valid_moves()) == {expected}
    before = game.get_state()
    reject(game, {"type": "move", "move": Move((2, 3), (4, 5)).to_json()})
    assert game.get_state() == before
    event = act(game, expected)
    assert {tuple(pos) for pos in event["captured"]} == {(3, 4), (5, 6)}
    after = game.get_state()
    assert piece(after, (3, 4)) is None and piece(after, (5, 6)) is None
    assert GameManager.from_snapshot(after).get_state() == after


def test_four_jump_king_cycle_returns_to_source_without_recapturing_a_piece():
    # The four distinct jumped men may be captured only once each (WCDF 1.20).
    # Both geometrically symmetric complete routes end back on the source.
    game = reference_game(
        [
            ("king", -1, (2, 3)),
            ("man", 1, (3, 2)),
            ("man", 1, (3, 4)),
            ("man", 1, (5, 2)),
            ("man", 1, (5, 4)),
            ("man", 1, (7, 0)),
        ]
    )
    clockwise = Move((2, 3), (2, 3), hops=((4, 5), (6, 3), (4, 1), (2, 3)))
    anticlockwise = Move((2, 3), (2, 3), hops=((4, 1), (6, 3), (4, 5), (2, 3)))
    assert set(game.get_valid_moves()) == {clockwise, anticlockwise}
    before = game.get_state()
    reject(game, {"type": "move", "move": Move((2, 3), (4, 5)).to_json()})
    assert game.get_state() == before
    event = act(game, clockwise)
    assert len(event["captured"]) == 4
    assert {tuple(s) for s in event["captured"]} == {
        (3, 2),
        (3, 4),
        (5, 2),
        (5, 4),
    }
    assert piece(game.get_state(), (2, 3))["kind"] == "king"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_crowning_finishes_turn_and_new_king_cannot_jump_back_same_turn():
    game = reference_game(
        [
            ("man", -1, (5, 0)),
            ("man", 1, (6, 1)),
            ("man", 1, (6, 3)),
            ("man", 1, (7, 6)),
        ]
    )
    assert set(game.get_valid_moves()) == {Move((5, 0), (7, 2))}
    event = act(game, Move((5, 0), (7, 2)))
    assert event["captured"] == [[6, 1]]
    after = game.get_state()
    assert piece(after, (7, 2))["kind"] == "king"
    assert piece(after, (6, 3))["side"] == 1
    assert after["active_side"] == 1
    assert GameManager.from_snapshot(after).get_state() == after


def test_no_remaining_or_no_available_opponent_move_is_decisive():
    capture = reference_game([("man", -1, (2, 1)), ("man", 1, (3, 2))])
    event = act(capture, Move((2, 1), (4, 3)))
    assert event["outcome"]["cause"] == "no_legal_moves"
    assert event["outcome"]["winner"] == "black"
    blocked = reference_game([("man", -1, (2, 1)), ("man", 1, (0, 1))])
    event = act(blocked, Move((2, 1), (3, 2)))
    assert event["outcome"]["cause"] == "no_legal_moves"
    assert event["outcome"]["winner"] == "black"
    reject(blocked, {"type": "resign"})


CYCLE = (
    Move((2, 1), (3, 2)),
    Move((5, 6), (4, 5)),
    Move((3, 2), (2, 1)),
    Move((4, 5), (5, 6)),
)


def kings():
    return reference_game([("king", -1, (2, 1)), ("king", 1, (5, 6))])


def test_wcdf_third_repetition_with_declared_next_move_not_moved_flag():
    # WCDF 1.32.1: demonstrate that the *next move* yields the third position.
    game = kings()
    for index in range(7):
        act(game, CYCLE[index % 4])
    before = game.get_state()
    assert before["halfmove_count"] == 7
    reject(
        game,
        {
            "type": "claim_draw",
            "claim": "threefold",
            "intended_move": Move((4, 5), (3, 4)).to_json(),
        },
    )
    assert game.get_state() == before
    event = claim(game, "threefold", intended=CYCLE[3])
    assert event["outcome"] == {
        "kind": "draw",
        "cause": "threefold",
        "winner": None,
    }
    after = game.get_state()
    assert after["board"] == before["board"]  # A prospective move is NOT played.
    assert GameManager.from_snapshot(after).get_state() == after


def test_no_progress_claim_requires_both_players_forty_moves():
    # WCDF 1.32.2: 40 previous moves *per player* = 80 halfmoves, no man
    # advance and no piece removed. King quiet moves increment the counter.
    game = kings()
    for index in range(79):
        act(game, CYCLE[index % 4])
    before = game.get_state()
    assert before["halfmove_count"] == 79
    reject(
        game,
        {"type": "claim_draw", "claim": "forty-move", "intended_move": None},
    )
    assert game.get_state() == before
    act(game, CYCLE[3])
    eligible = game.get_state()
    assert eligible["halfmove_count"] == 80
    event = claim(game, "forty-move")
    assert event["outcome"] == {
        "kind": "draw",
        "cause": "forty-move",
        "winner": None,
    }
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_uncrowned_man_advancement_resets_no_progress_even_without_capture():
    game = reference_game(
        [
            ("king", -1, (2, 1)),
            ("man", -1, (2, 5)),
            ("king", 1, (5, 6)),
        ]
    )
    act(game, Move((2, 1), (3, 0)))
    act(game, Move((5, 6), (4, 7)))
    assert game.get_state()["halfmove_count"] == 2
    act(game, Move((2, 5), (3, 4)))
    assert game.get_state()["halfmove_count"] == 0
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_premature_claim_wrong_actor_timeout_and_resignation_are_atomic():
    game = kings()
    for name in ("threefold", "forty-move"):
        reject(
            game,
            {"type": "claim_draw", "claim": name, "intended_move": None},
            action_id=f"premature-{name}",
        )
    reject(game, {"type": "timeout"}, action_id="premature-timeout")
    # Resignation by either side is supported; the active player resigns here.
    before = game.get_state()
    event = game.submit_action("black", 0, "black-resigns", {"type": "resign"}, 1)
    assert event["outcome"]["cause"] == "resignation"
    assert event["outcome"]["winner"] == "white"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()
    reject(game, {"type": "resign"})
    timed = kings()
    pre = timed.get_state()
    result = timed.submit_action("black", 0, "flag-black", {"type": "timeout"}, 600001)
    assert result["outcome"]["cause"] == "timeout"
    assert result["outcome"]["winner"] == "white"
    assert timed.get_state()["revision"] == pre["revision"] + 1
    assert GameManager.from_snapshot(timed.get_state()).get_state() == timed.get_state()
