"""WCDF 1.15–1.21 and 1.30 through the shipped declarative game definition.

The JSON remains non-playable until draw, clock and complete-game gates pass.
Rule source: https://wcdf.net/rules/rules_of_checkers_english.pdf
"""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move

CONFIG = Path(__file__).parents[1] / "packages/english_draughts/config.json"


def session(placements=None, starting_side=1):
    """Create a real game, optionally using the supported configured initial board."""
    data = json.loads(CONFIG.read_text())
    if placements is not None:
        data["starting_side"] = starting_side
        data["board"]["starting_pieces"] = [
            {"piece": kind, "color": color, "squares": [list(square) for square in squares]}
            for kind, color, squares in placements
        ]
    return GameManager(validate_definition(data), "english", ("white", "red"), 0)


def test_initial_board_offers_seven_moves_and_preserves_read_only_state():
    game = session()
    before = game.get_state()
    moves = game.get_valid_moves()
    assert len(moves) == 7
    assert before["active_side"] == -1
    assert before["participants"]["-1"] == "red"
    assert all(move.start_pos[0] == 2 and move.end_pos[0] == 3 for move in moves)
    assert game.get_state() == before
    assert before["config"]["playable"] is False


@pytest.mark.parametrize("destination", [(6, 3), (3, 4), (4, 2), (4, 4)])
def test_uncrowned_man_cannot_move_backward_long_orthogonal_or_jump_empty(destination):
    game = session([("man", "white", [(5, 2)]), ("man", "black", [(0, 1)])])
    before = game.get_state()
    move = Move((5, 2), destination)
    assert move not in game.get_valid_moves()
    with pytest.raises(TransitionError):
        game.submit("white", 0, "illegal", move, 1)
    assert game.get_state() == before


def test_capture_is_compulsory_and_full_chain_is_one_atomic_action():
    game = session(
        [
            ("man", "white", [(5, 2), (5, 6)]),
            ("man", "black", [(4, 3), (2, 5), (0, 1)]),
        ]
    )
    before = game.get_state()
    full = Move((5, 2), (1, 6), ((3, 4), (1, 6)))
    assert game.get_valid_moves() == [full]
    for move in [Move((5, 6), (4, 7)), Move((5, 2), (3, 4))]:
        with pytest.raises(TransitionError):
            game.submit("white", 0, "rejected", move, 1)
        assert game.get_state() == before
    event = game.submit("white", 0, "chain", full, 1)
    state = game.get_state()
    assert event["captured"] == [[4, 3], [2, 5]]
    assert state["revision"] == 1 and len(state["events"]) == 1
    assert state["halfmove_count"] == 0 and state["active_side"] == -1
    assert len(state["captured"]) == 2
    assert GameManager.from_snapshot(state).get_state() == state
    assert game.submit("white", 0, "chain", full, 99) == event
    assert game.get_state() == state


def test_player_may_choose_a_shorter_capture_instead_of_maximum():
    game = session(
        [
            ("man", "white", [(5, 0), (7, 6)]),
            ("man", "black", [(4, 1), (2, 3), (6, 5)]),
        ]
    )
    short = Move((7, 6), (5, 4))
    long = Move((5, 0), (1, 4), ((3, 2), (1, 4)))
    assert set(game.get_valid_moves()) == {short, long}
    event = game.submit("white", 0, "short", short, 1)
    assert event["captured"] == [[6, 5]]
    assert len(game.get_state()["captured"]) == 1


def test_crowning_ends_capture_even_when_new_king_could_continue_backward():
    game = session(
        [
            ("man", "white", [(2, 1)]),
            ("man", "black", [(1, 2), (1, 4), (6, 7)]),
        ]
    )
    crown = Move((2, 1), (0, 3))
    assert game.get_valid_moves() == [crown]
    before = game.get_state()
    with pytest.raises(TransitionError):
        game.submit("white", 0, "continued", Move((2, 1), (2, 5), ((0, 3), (2, 5))), 1)
    assert game.get_state() == before
    event = game.submit("white", 0, "crown", crown, 1)
    state = game.get_state()
    assert event["captured"] == [[1, 2]]
    assert {"square": [0, 3], "kind": "king", "side": 1, "moved": True} in state["board"]
    assert any(piece["square"] == [1, 4] for piece in state["board"])
    assert GameManager.from_snapshot(state).get_state() == state


def test_short_king_moves_backward_but_cannot_fly():
    game = session([("king", "white", [(3, 2)]), ("man", "black", [(7, 6)])])
    assert {move.end_pos for move in game.get_valid_moves()} == {(2, 1), (2, 3), (4, 1), (4, 3)}
    before = game.get_state()
    with pytest.raises(TransitionError):
        game.submit("white", 0, "flying", Move((3, 2), (6, 5)), 1)
    assert game.get_state() == before
    game.submit("white", 0, "backward", Move((3, 2), (4, 3)), 1)
    assert game.get_state()["halfmove_count"] == 1


@pytest.mark.parametrize("remaining", [[], [(7, 0)]])
def test_last_legal_move_wins_when_opponent_is_eliminated_or_blocked(remaining):
    game = session(
        [
            ("man", "white", [(5, 2)]),
            ("man", "black", [(4, 3), *remaining]),
        ]
    )
    event = game.submit("white", 0, "last", Move((5, 2), (3, 4)), 1)
    state = game.get_state()
    assert state["outcome"] == {
        "kind": "win",
        "cause": "no_legal_moves",
        "winner": "white",
        "priority": 100,
    }
    assert event["outcome"] == state["outcome"]
    before = deepcopy(state)
    with pytest.raises(TransitionError):
        game.submit("red", 1, "after-game", Move((7, 0), (6, 1)), 2)
    assert game.get_state() == before
    assert GameManager.from_snapshot(state).get_state() == state


@pytest.mark.parametrize("side", [1, -1])
def test_man_cannot_capture_backward_on_either_side(side):
    start, enemy, landing = (5, 2), (6, 3), (7, 4)
    if side == -1:
        start, enemy, landing = [
            tuple(7 - axis for axis in square) for square in (start, enemy, landing)
        ]
    own_color, enemy_color = ("white", "black") if side == 1 else ("black", "white")
    game = session([("man", own_color, [start]), ("man", enemy_color, [enemy])], starting_side=side)
    before = game.get_state()
    forbidden = Move(start, landing)
    assert forbidden not in game.get_valid_moves()
    with pytest.raises(TransitionError):
        game.submit("white" if side == 1 else "red", 0, "backward-capture", forbidden, 1)
    assert game.get_state() == before


@pytest.mark.parametrize("side", [1, -1])
@pytest.mark.parametrize("capture", [False, True])
def test_quiet_and_capture_crowning_are_symmetric_and_preserve_result(side, capture):
    start = (2, 1) if capture else (1, 2)
    end = (0, 3)
    enemy_squares = [(1, 2)] if capture else [(6, 7)]
    if side == -1:
        start, end = [tuple(7 - axis for axis in square) for square in (start, end)]
        enemy_squares = [tuple(7 - axis for axis in square) for square in enemy_squares]
    own_color, enemy_color = ("white", "black") if side == 1 else ("black", "white")
    game = session(
        [("man", own_color, [start]), ("man", enemy_color, enemy_squares)], starting_side=side
    )
    actor = "white" if side == 1 else "red"
    event = game.submit(actor, 0, "promotion", Move(start, end), 1)
    saved = game.get_state()
    assert {"square": list(end), "kind": "king", "side": side, "moved": True} in saved["board"]
    assert len(event["captured"]) == int(capture)
    assert saved["halfmove_count"] == 0
    if capture:
        assert saved["outcome"]["winner"] == actor
    assert GameManager.from_snapshot(saved).get_state() == saved


def test_advancing_a_man_resets_actual_accumulated_no_progress_counter():
    game = session(
        [("king", "white", [(7, 0)]), ("man", "white", [(5, 4)]), ("king", "black", [(0, 7)])]
    )
    game.submit("white", 0, "king-one", Move((7, 0), (6, 1)), 1)
    game.submit("red", 1, "king-two", Move((0, 7), (1, 6)), 2)
    assert game.get_state()["halfmove_count"] == 2
    game.submit("white", 2, "man-advance", Move((5, 4), (4, 3)), 3)
    saved = game.get_state()
    assert saved["halfmove_count"] == 0
    assert GameManager.from_snapshot(saved).get_state() == saved


def test_king_must_complete_turning_capture_and_cannot_fly_over_distant_enemy():
    game = session([("king", "white", [(3, 2)]), ("man", "black", [(2, 3), (2, 5)])])
    complete = Move((3, 2), (3, 6), ((1, 4), (3, 6)))
    assert game.get_valid_moves() == [complete]
    before = game.get_state()
    with pytest.raises(TransitionError):
        game.submit("white", 0, "partial", Move((3, 2), (1, 4)), 1)
    assert game.get_state() == before
    assert game.submit("white", 0, "full", complete, 1)["captured"] == [[2, 3], [2, 5]]
    distant = session([("king", "white", [(5, 0)]), ("man", "black", [(3, 2)])])
    before = distant.get_state()
    with pytest.raises(TransitionError):
        distant.submit("white", 0, "flying", Move((5, 0), (2, 3)), 1)
    assert distant.get_state() == before
