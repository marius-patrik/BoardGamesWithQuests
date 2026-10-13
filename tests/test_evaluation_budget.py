"""FR-69/80: aggregate evaluation limits reject hostile work without partial state."""

import json
from pathlib import Path

import pytest

from engine.model.game.board import Board
from engine.model.game.capture_geometry import (
    CaptureEnumerator,
    CapturePolicy,
    EvaluationBudget,
    EvaluationBudgetExceeded,
)
from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move
from engine.model.pieces.piece import Piece


def definition(*, hostile: bool = False):
    """Build validated neutral inputs, including the permitted maximum board load."""
    source = json.loads(
        (Path(__file__).parents[1] / "packages/english_draughts/config.json").read_text()
    )
    source["pieces"] = {"man": source["pieces"]["man"]}
    source["pieces"]["man"].update(moves=[[0, 1]], attacks=[[1, 0]], color_relative=False)
    if not hostile:
        source["pieces"]["man"].pop("capture_policy")
    source["board"] = {
        "rows": 64 if hostile else 8,
        "columns": 64 if hostile else 8,
        "starting_pieces": [
            {
                "piece": "man",
                "color": "white",
                "squares": (
                    [[row, col] for row in range(32) for col in range(0, 64, 2)]
                    if hostile
                    else [[0, 0]]
                ),
            },
            {
                "piece": "man",
                "color": "black",
                "squares": (
                    [[row, col] for row in range(32, 64) for col in range(0, 64, 2)]
                    if hostile
                    else [[7, 7]]
                ),
            },
        ],
    }
    source["rules"] = [
        {
            "id": "permit",
            "hook": "permits_move",
            "when": {"op": "true"},
            "effects": [{"op": "permit", "params": {}}],
        }
    ]
    return validate_definition(source)


def session(*, hostile: bool = False) -> GameManager:
    return GameManager(definition(hostile=hostile), "budget-game", ("alice", "bob"), 0)


def measured_operation(action: str) -> int:
    game = session()
    budget = EvaluationBudget(1000000)
    with game._lock, game._operation(budget):
        if action == "read":
            assert [move.to_json() for move in game.get_valid_moves()] == [
                {"start": [0, 0], "hops": [[0, 1]], "promotion": None}
            ]
        else:
            assert game.submit("alice", 0, "move-one", Move((0, 0), (0, 1)), 1)["revision"] == 1
    return budget.used


@pytest.mark.parametrize("action", ["read", "submit"])
def test_exact_aggregate_boundary_accepts_complete_ordinary_operation(action: str) -> None:
    required = measured_operation(action)
    assert required > 1
    game = session()
    budget = EvaluationBudget(required)
    with game._lock, game._operation(budget):
        if action == "read":
            assert len(game.get_valid_moves()) == 1
        else:
            assert game.submit("alice", 0, "move-one", Move((0, 0), (0, 1)), 1)["revision"] == 1
    assert budget.used == required


@pytest.mark.parametrize("action", ["read", "submit"])
def test_one_unit_below_boundary_rejects_without_any_state_change(action: str) -> None:
    game = session()
    before = game.get_state()
    budget = EvaluationBudget(measured_operation(action) - 1)
    with pytest.raises(EvaluationBudgetExceeded, match="aggregate"):
        with game._lock, game._operation(budget):
            if action == "read":
                game.get_valid_moves()
            else:
                game.submit("alice", 0, "move-one", Move((0, 0), (0, 1)), 1)
    assert game.get_state() == before
    assert game._evaluation is None
    assert len(game.get_valid_moves()) == 1
    accepted = game.submit("alice", 0, "move-one", Move((0, 0), (0, 1)), 1)
    assert accepted["revision"] == 1


@pytest.mark.parametrize("action", ["read", "submit"])
def test_permitted_maximum_board_and_piece_input_fails_closed(action: str) -> None:
    game = session(hostile=True)
    before = game.get_state()
    assert len(before["board"]) == 2048
    assert game.definition.board["rows"] * game.definition.board["columns"] == 4096
    with pytest.raises(EvaluationBudgetExceeded, match="aggregate"):
        if action == "read":
            game.get_valid_moves()
        else:
            game.submit("alice", 0, "hostile-intent", Move((0, 0), (0, 1)), 1)
    assert game.get_state() == before
    assert game._evaluation is None


def test_hostile_replay_cannot_reset_budget_for_each_event() -> None:
    # Reconstructing this permitted large position must reject its expensive action
    # through the same bounded executor, rather than trusting the supplied end state.
    snapshot = session(hostile=True).get_state()
    snapshot["events"] = [
        {
            "actor": "alice",
            "expected_revision": 0,
            "action_id": "hostile-intent",
            "at_ms": 1,
            "move": Move((0, 0), (0, 1)).to_json(),
        }
    ]
    with pytest.raises(TransitionError, match="aggregate"):
        GameManager.from_snapshot(snapshot)


def test_normal_replay_and_exact_retry_preserve_authoritative_outputs() -> None:
    game = session()
    event = game.submit("alice", 0, "move-one", Move((0, 0), (0, 1)), 1)
    expected = game.get_state()
    recovered = GameManager.from_snapshot(expected)
    assert recovered.get_state() == expected
    assert recovered.submit("alice", 0, "move-one", Move((0, 0), (0, 1)), 50) == event
    assert recovered.get_state() == expected
    assert recovered._evaluation is None


def capture_board() -> Board:
    attacker = Piece(1, "token", vectors=[(-1, 1)], attack_vectors=[(-1, 1)])
    victim = Piece(-1, "token", vectors=[(1, -1)], attack_vectors=[(1, -1)])
    return Board((6, 6), [((5, 0), attacker), ((4, 1), victim)])


def test_capture_enumerations_share_budget_across_repeated_searches() -> None:
    board = capture_board()
    policy = CapturePolicy(False, False, False, 100)
    measure = EvaluationBudget(1000)
    expected = CaptureEnumerator(board, measure).enumerate((5, 0), policy)
    one_search = measure.used
    assert expected == [{"start": [5, 0], "steps": [{"landing": [3, 2], "captured": [4, 1]}]}]
    budget = EvaluationBudget(2 * one_search - 1)
    search = CaptureEnumerator(board, budget)
    assert search.enumerate((5, 0), policy) == expected
    with pytest.raises(EvaluationBudgetExceeded):
        search.enumerate((5, 0), policy)
    assert board.get_piece_at((4, 1)).getColor() == -1
    assert board.get_piece_at((5, 0)).getColor() == 1


@pytest.mark.parametrize("units", [-1, True, 1.5])
def test_invalid_work_reservations_do_not_consume_budget(units: object) -> None:
    budget = EvaluationBudget(1)
    with pytest.raises(ValueError):
        budget.consume(units)
    assert budget.used == 0
    budget.consume(1)
    with pytest.raises(EvaluationBudgetExceeded):
        budget.consume()
    assert budget.used == 1


def test_exact_position_cache_is_detached_and_invalidates_after_board_change() -> None:
    data = session().get_state()["config"]
    data["pieces"]["man"].update(
        moves=[[-1, 1]],
        attacks=[[-1, 1]],
        capture_policy={
            "flying": False,
            "land_anywhere": False,
            "deferred_removal": False,
            "max_nodes": 100,
        },
    )
    data["board"]["starting_pieces"] = [
        {"piece": "man", "color": "white", "squares": [[5, 0]]},
        {"piece": "man", "color": "black", "squares": [[4, 1]]},
    ]
    game = GameManager(validate_definition(data), "cache", ("alice", "bob"), 0)
    budget = EvaluationBudget(100000)
    with game._lock, game._operation(budget):
        board = game._board(game.get_state())
        baseline = budget.used
        first = game._paths(board, 1)
        first_cost = budget.used - baseline
        baseline = budget.used
        expected = game._paths(board, 1)
        cached_cost = budget.used - baseline
        assert cached_cost < first_cost
        first[0]["steps"][0]["captured"][0] = 99
        assert game._paths(board, 1) == expected
        board.set_piece_at((4, 1), None)
        assert game._paths(board, 1) == []
    assert game._evaluation is None
    assert game.get_state()["revision"] == 0


def test_every_accepted_action_in_long_history_remains_recoverable() -> None:
    data = session().get_state()["config"]
    data["pieces"]["man"].update(moves=[[0, 1], [0, -1]], attacks=[[0, 1], [0, -1]])
    data["board"]["starting_pieces"][1]["squares"] = [[7, 0]]
    game = GameManager(validate_definition(data), "long-transcript", ("alice", "bob"), 0)
    for turn in range(120):
        row = 0 if turn % 2 == 0 else 7
        col = (turn // 2) % 2
        game.submit(
            "alice" if row == 0 else "bob",
            turn,
            str(turn),
            Move((row, col), (row, 1 - col)),
            turn + 1,
        )
    snapshot = game.get_state()
    assert snapshot["revision"] == 120
    recovered = GameManager.from_snapshot(snapshot)
    assert recovered.get_state() == snapshot
    original = snapshot["events"][0]
    assert recovered.submit("alice", 0, "0", Move((0, 0), (0, 1)), 999) == original
    assert recovered.get_state() == snapshot
    assert recovered._evaluation is None
    assert game.get_state() == snapshot


@pytest.mark.parametrize("parent_limit,child_limit", [(2, 3), (3, 2)])
def test_parent_and_child_reservations_are_atomic(parent_limit: int, child_limit: int) -> None:
    parent = EvaluationBudget(parent_limit)
    child = EvaluationBudget(child_limit, parent=parent)
    child.consume(1)
    assert parent.used == child.used == 1
    with pytest.raises(EvaluationBudgetExceeded):
        child.consume(2)
    assert parent.used == child.used == 1
    child.consume(1)
    assert parent.used == child.used == 2


def test_separate_replay_children_share_a_monotonic_parent() -> None:
    parent = EvaluationBudget(3)
    first = EvaluationBudget(2, parent=parent)
    second = EvaluationBudget(2, parent=parent)
    first.consume(2)
    assert parent.used == 2
    with pytest.raises(EvaluationBudgetExceeded):
        second.consume(2)
    assert second.used == 0 and parent.used == 2
    second.consume(1)
    assert second.used == 1 and parent.used == 3


def test_parent_cannot_allow_a_child_to_exceed_per_action_ceiling() -> None:
    parent = EvaluationBudget(100)
    child = EvaluationBudget(1, parent=parent)
    with pytest.raises(EvaluationBudgetExceeded):
        child.consume(2)
    assert child.used == parent.used == 0
