"""Independent FR-69/80 checks of atomic resources and durable bounded actions."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from engine.model.game.capture_geometry import EvaluationBudget, EvaluationBudgetExceeded
from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move

ROOT = Path(__file__).resolve().parents[1]


def data(*, hostile: bool = False) -> dict:
    """Create explicit neutral motion and an optional maximum-size capture load."""
    result = json.loads((ROOT / "packages/english_draughts/config.json").read_text())
    result.update(name="budget-contract", title="Budget authority", playable=False)
    mover = result["pieces"]["man"]
    result.pop("starting_side", None)
    result.pop("halfmove_reset", None)
    mover.pop("promotion", None)
    mover.update(moves=[[0, 1], [0, -1]], attacks=[[1, 0]], color_relative=False)
    if not hostile:
        mover.pop("capture_policy")
    result["pieces"] = {"token": mover}
    result["board"] = {
        "rows": 64 if hostile else 8,
        "columns": 64 if hostile else 8,
        "starting_pieces": [
            {
                "piece": "token",
                "color": "white",
                "squares": (
                    [[row, col] for row in range(32) for col in range(0, 64, 2)]
                    if hostile
                    else [[0, 0]]
                ),
            },
            {
                "piece": "token",
                "color": "black",
                "squares": (
                    [[row, col] for row in range(32, 64) for col in range(0, 64, 2)]
                    if hostile
                    else [[7, 0]]
                ),
            },
        ],
    }
    result["rules"] = [
        {
            "id": "authorize",
            "hook": "permits_move",
            "when": {"op": "true"},
            "effects": [{"op": "permit", "params": {}}],
        }
    ]
    result["quests"] = []
    result["clock"] = {"initial_seconds": 30, "increment_seconds": 0}
    return result


def game(*, hostile: bool = False) -> GameManager:
    """Instantiate actual configured authority without implementation test doubles."""
    return GameManager(
        validate_definition(data(hostile=hostile)), "independent-budget", ("alice", "bob"), 0
    )


def canonical(value: dict) -> str:
    """Compare externally persistable JSON including exact scalar representation."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@pytest.mark.parametrize("exhausted", ["grandparent", "parent", "child"])
def test_failed_three_level_reservation_changes_no_ancestor(exhausted: str) -> None:
    """FR-69: every level reserves atomically even when a distant ancestor denies."""
    root = EvaluationBudget(2 if exhausted == "grandparent" else 10)
    middle = EvaluationBudget(2 if exhausted == "parent" else 10, parent=root)
    child = EvaluationBudget(2 if exhausted == "child" else 10, parent=middle)
    child.consume(1)
    with pytest.raises(EvaluationBudgetExceeded):
        child.consume(2)
    assert (root.used, middle.used, child.used) == (1, 1, 1)
    child.consume(1)
    assert (root.used, middle.used, child.used) == (2, 2, 2)


def test_cyclic_parent_denies_without_leaking_partial_work() -> None:
    """FR-69: corrupted trusted hierarchy never changes any traversed counter."""
    root = EvaluationBudget(10)
    child = EvaluationBudget(10, parent=root)
    root.parent = child
    with pytest.raises(ValueError, match="acyclic"):
        child.consume(1)
    assert root.used == child.used == 0
    root.parent = None
    child.consume(1)
    assert root.used == child.used == 1


def test_accepted_120_action_history_replays_canonical_json_and_accepts_later_action() -> None:
    """FR-80: accepted history remains exact and usable beyond replay and retry."""
    original = game()
    events = []
    for revision in range(120):
        row = 0 if revision % 2 == 0 else 7
        start = (revision // 2) % 2
        events.append(
            original.submit(
                "alice" if row == 0 else "bob",
                revision,
                f"action-{revision}",
                Move((row, start), (row, 1 - start)),
                revision + 1,
            )
        )
    snapshot = original.get_state()
    assert len(snapshot["events"]) == snapshot["revision"] == 120
    recovered = GameManager.from_snapshot(snapshot)
    assert canonical(recovered.get_state()) == canonical(snapshot)
    retry = recovered.submit("alice", 0, "action-0", Move((0, 0), (0, 1)), 999999)
    assert canonical(retry) == canonical(events[0])
    retry["move"]["hops"][0][0] = 99
    assert canonical(recovered.get_state()) == canonical(snapshot)
    later = recovered.submit("alice", 120, "action-120", Move((0, 0), (0, 1)), 121)
    expected = original.submit("alice", 120, "action-120", Move((0, 0), (0, 1)), 121)
    assert canonical(later) == canonical(expected)
    assert canonical(recovered.get_state()) == canonical(original.get_state())
    assert canonical(GameManager.from_snapshot(recovered.get_state()).get_state()) == canonical(
        original.get_state()
    )


def test_repeated_hostile_failures_leave_authority_and_unrelated_work_unchanged() -> None:
    """FR-69/80: rejected resource loads cannot warm a cache into authorization."""
    overloaded = game(hostile=True)
    before = canonical(overloaded.get_state())
    for attempt in range(2):
        with pytest.raises(EvaluationBudgetExceeded):
            overloaded.submit("alice", 0, f"overload-{attempt}", Move((0, 0), (0, 1)), 1)
        assert canonical(overloaded.get_state()) == before
        with pytest.raises(EvaluationBudgetExceeded):
            overloaded.get_valid_moves()
        assert canonical(overloaded.get_state()) == before
    ordinary = game()
    assert ordinary.submit("alice", 0, "ordinary", Move((0, 0), (0, 1)), 1)["revision"] == 1


def test_replay_global_capacity_cannot_authorize_one_hostile_action() -> None:
    """FR-69: a large replay allowance never expands an individual move's ceiling."""
    manager = game(hostile=True)
    initial = manager.get_state()
    supplied = deepcopy(initial)
    supplied["events"] = [
        {
            "revision": 1,
            "expected_revision": 0,
            "actor": "alice",
            "action_id": "overload",
            "at_ms": 1,
            "move": Move((0, 0), (0, 1)).to_json(),
            "captured": [],
            "effects": [],
            "outcome": None,
        }
    ]
    supplied["revision"] = 1
    with pytest.raises(TransitionError, match="aggregate"):
        GameManager.from_snapshot(supplied)
    assert canonical(manager.get_state()) == canonical(initial)
