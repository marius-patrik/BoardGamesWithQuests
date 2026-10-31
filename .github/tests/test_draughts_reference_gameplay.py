"""English-draughts rulebook exercised through real revisioned game sessions."""

from __future__ import annotations

from importlib import resources
import json

import pytest

from model.resources import bundled_games_root
from model.definition import validate_definition
from model.manager import GameManager, TransitionError
from model.move import Move


def session(pieces, *, starting_side=-1):
    """Open a real game with a public consumer-provided legal starting position."""
    data = json.loads(bundled_games_root().joinpath("checkers", "config.json").read_text())
    data["starting_side"] = starting_side
    data["board"]["starting_pieces"] = [
        {
            "piece": kind,
            "color": "white" if side == 1 else "black",
            "squares": [list(square)],
        }
        for kind, side, square in pieces
    ]
    return GameManager(validate_definition(data), "draughts-reference", ("white", "black"), 0)


def submit(manager, move):
    state = manager.get_state()
    side = str(state["active_side"])
    return manager.submit(
        state["participants"][side],
        state["revision"],
        "move-" + str(state["revision"]),
        move,
        state["revision"] + 1,
    )


def reject(manager, move):
    before = manager.get_state()
    with pytest.raises(TransitionError):
        submit(manager, move)
    assert manager.get_state() == before


def test_short_kings_move_only_one_square_when_no_capture_is_available():
    game = session(
        [
            ("king", -1, (2, 3)),
            ("man", 1, (7, 0)),
        ]
    )
    actions = game.get_valid_moves()
    assert Move((2, 3), (3, 2)) in actions
    assert Move((2, 3), (3, 4)) in actions
    assert Move((2, 3), (4, 5)) not in actions
    reject(game, Move((2, 3), (4, 5)))


def test_capture_is_compulsory_and_complete_multijump_is_atomic():
    game = session(
        [
            ("man", -1, (2, 1)),
            ("man", 1, (3, 2)),
            ("man", 1, (5, 4)),
            ("man", 1, (7, 6)),
        ]
    )
    expected = Move((2, 1), (6, 5), hops=((4, 3), (6, 5)))
    assert expected in game.get_valid_moves()
    reject(game, Move((2, 1), (3, 0)))
    reject(game, Move((2, 1), (4, 3)))
    before = game.get_state()
    event = submit(game, expected)
    state = game.get_state()
    assert state["revision"] == before["revision"] + 1
    assert set(map(tuple, event["captured"])) == {(3, 2), (5, 4)}
    assert any(p["square"] == [6, 5] and p["side"] == -1 for p in state["board"])
    assert not any(p["square"] in ([3, 2], [5, 4]) for p in state["board"])
    assert GameManager.from_snapshot(state).get_state() == state


def test_alternative_capture_routes_are_distinct_exact_legal_intents():
    game = session(
        [
            ("man", -1, (2, 3)),
            ("man", 1, (3, 2)),
            ("man", 1, (3, 4)),
            ("man", 1, (7, 6)),
        ]
    )
    moves = game.get_valid_moves()
    a = Move((2, 3), (4, 1))
    b = Move((2, 3), (4, 5))
    assert a in moves and b in moves
    assert a != b
    reject(game, Move((2, 3), (3, 2)))


def test_english_draughts_crowning_ends_capture_turn_before_new_king_jump():
    game = session(
        [
            ("man", -1, (5, 0)),
            ("man", 1, (6, 1)),
            ("man", 1, (6, 3)),
            ("man", 1, (7, 6)),
        ]
    )
    destination = Move((5, 0), (7, 2))
    assert destination in game.get_valid_moves()
    assert all(len(m.hops) == 1 for m in game.get_valid_moves() if m.start_pos == (5, 0))
    event = submit(game, destination)
    state = game.get_state()
    assert event["captured"] == [[6, 1]]
    assert any(p["square"] == [7, 2] and p["kind"] == "king" for p in state["board"])
    assert any(p["square"] == [6, 3] for p in state["board"])
    assert GameManager.from_snapshot(state).get_state() == state


def test_last_opponent_piece_captured_causes_game_over_and_replay():
    game = session(
        [
            ("man", -1, (2, 1)),
            ("man", 1, (3, 2)),
        ]
    )
    event = submit(game, Move((2, 1), (4, 3)))
    assert event["outcome"] is not None
    assert event["outcome"]["kind"] == "win"
    assert event["outcome"]["winner"] == "black"
    assert game.get_valid_moves() == []
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()
