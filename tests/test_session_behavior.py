"""FR-10/12/13/23/62/63: observable authoritative session behavior and replay."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path

import pytest

from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move

ROOT = Path(__file__).resolve().parents[1]


def definition(*, capture=False, effects=(), deny=False, outcome=False):
    data = json.loads((ROOT / "packages/english_draughts/config.json").read_text())
    data["name"] = "neutral-session"
    for option in ("starting_side", "halfmove_reset", "position_identity", "initial_state"):
        data.pop(option, None)
    for piece in data["pieces"].values():
        piece.pop("promotion", None)
    data["board"] = {
        "rows": 6,
        "columns": 6,
        "starting_pieces": [
            {"piece": "man", "color": "white", "squares": [[5, 0]]},
            {
                "piece": "man",
                "color": "black",
                "squares": [[4, 1], [2, 3]] if capture else [[0, 5]],
            },
        ],
    }
    # The fixture declares behavior explicitly; it is not a shipped rulebook claim.
    data["rules"] = [
        {
            "id": "permit",
            "hook": "permits_move",
            "when": {"op": "true"},
            "effects": [{"op": "permit", "params": {}}],
        },
    ]
    if deny:
        data["rules"].append(
            {
                "id": "deny",
                "hook": "permits_move",
                "when": {"op": "true"},
                "effects": [{"op": "deny", "params": {"reason": "denied"}}],
            }
        )
    if effects:
        data["rules"].append(
            {
                "id": "effects",
                "hook": "on_move_made",
                "when": {"op": "true"},
                "effects": list(effects),
            }
        )
    if outcome:
        data["rules"].append(
            {
                "id": "terminal",
                "hook": "outcome",
                "when": {"op": "true"},
                "effects": [
                    {
                        "op": "propose_outcome",
                        "params": {
                            "kind": "win",
                            "cause": "configured-objective",
                            "winner": 1,
                            "priority": 10,
                        },
                    }
                ],
            }
        )
    data["quests"] = [
        {
            "id": "participate",
            "description": "Complete an authorized action",
            "when": {"op": "true"},
            "reward": 10,
        }
    ]
    data["clock"] = {"initial_seconds": 60, "increment_seconds": 2}
    return validate_definition(data)


def session(**options):
    return GameManager(definition(**options), "test-game", ("alice", "bob"), 1000)


def test_legal_action_updates_one_revision_clocks_quests_and_recovers_after_restart():
    game = session(
        effects=[
            {"op": "increment_state", "params": {"name": "moves", "amount": 1}},
            {"op": "record_event", "params": {"name": "played", "payload": {"ok": True}}},
        ]
    )
    initial = game.get_state()
    move = Move((5, 0), (4, 1))
    assert move in game.get_valid_moves()
    assert game.get_state() == initial
    event = game.submit("alice", 0, "alice-1", move, 2500)
    state = game.get_state()
    assert state["board"][1]["square"] == [4, 1]
    assert state["active_side"] == -1
    assert state["revision"] == 1
    assert state["clocks"]["remaining_ms"] == {"1": 60500, "-1": 60000}
    assert state["rule_state"] == {"moves": 1}
    assert state["quest_progress"]["alice"]["participate"]["completed"] is True
    assert state["quest_progress"]["bob"]["participate"]["completed"] is False
    assert event["effects"] == [{"name": "played", "payload": {"ok": True}}]
    restored = GameManager.from_snapshot(json.loads(json.dumps(state)))
    assert restored.get_state() == state
    restored.submit("bob", 1, "bob-1", Move((0, 5), (1, 4)), 3500)
    assert restored.get_state()["revision"] == 2
    assert game.get_state() == state


def test_exact_retry_returns_saved_event_without_charging_clocks_or_repeating_rewards():
    game = session()
    move = Move((5, 0), (4, 1))
    event = game.submit("alice", 0, "once", move, 2000)
    committed = game.get_state()
    assert game.submit("alice", 0, "once", move, 500000) == event
    assert game.get_state() == committed
    event["move"]["start"][0] = 0
    assert game.get_state() == committed
    with pytest.raises(TransitionError):
        game.submit("alice", 0, "once", Move((5, 0), (4, 3)), 500000)
    assert game.get_state() == committed


@pytest.mark.parametrize(
    "actor,revision,move,time",
    [
        ("outsider", 0, Move((5, 0), (4, 1)), 2000),
        ("bob", 0, Move((5, 0), (4, 1)), 2000),
        ("alice", 1, Move((5, 0), (4, 1)), 2000),
        ("alice", True, Move((5, 0), (4, 1)), 2000),
        ("alice", 0, Move((5, 0), (4, 3)), 2000),
        ("alice", 0, Move((5, 0), (9, 3)), 2000),
        ("alice", 0, Move((5, 0), (4, 1)), 999),
        ("alice", 0, Move((5, 0), (4, 1)), True),
        ("alice", 0, Move((5, 0), (4, 1)), 61000),
    ],
)
def test_denied_action_leaves_entire_snapshot_unchanged(actor, revision, move, time):
    game = session()
    initial = game.get_state()
    with pytest.raises(TransitionError):
        game.submit(actor, revision, "denied", move, time)
    assert game.get_state() == initial


def test_deny_has_precedence_over_permit_without_side_effects():
    game = session(deny=True)
    before = game.get_state()
    assert game.get_valid_moves() == []
    with pytest.raises(TransitionError):
        game.submit("alice", 0, "denied", Move((5, 0), (4, 1)), 1000)
    assert game.get_state() == before


def test_complete_capture_chain_commits_once_and_rejects_truncated_intent():
    game = session(capture=True)
    before = game.get_state()
    partial = Move((5, 0), (3, 2))
    with pytest.raises(TransitionError):
        game.submit("alice", 0, "partial", partial, 2000)
    assert game.get_state() == before
    move = Move((5, 0), (1, 4), ((3, 2), (1, 4)))
    assert move in game.get_valid_moves()
    game.submit("alice", 0, "chain", move, 2000)
    state = game.get_state()
    assert state["board"] == [{"square": [1, 4], "kind": "man", "side": 1, "moved": True}]
    assert state["captured"] == [{"kind": "man", "side": -1}, {"kind": "man", "side": -1}]
    assert state["revision"] == 1
    assert GameManager.from_snapshot(state).get_state() == state


def test_later_effect_failure_rolls_back_board_clock_rule_state_and_event():
    game = session(
        effects=[
            {"op": "set_state", "params": {"name": "changed", "value": True}},
            {"op": "capture_piece", "params": {"square": [5, 5]}},
        ]
    )
    before = game.get_state()
    with pytest.raises(TransitionError):
        game.submit("alice", 0, "rollback", Move((5, 0), (4, 1)), 3000)
    assert game.get_state() == before


def test_same_revision_concurrent_actions_commit_exactly_once():
    game = session()

    def act(action_id):
        try:
            return game.submit("alice", 0, action_id, Move((5, 0), (4, 1)), 2000)
        except TransitionError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(act, ["one", "two"]))
    assert sum(result is not None for result in results) == 1
    assert game.get_state()["revision"] == 1
    assert len(game.get_state()["events"]) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("revision", 4),
        ("active_side", 1),
        ("outcome", {"kind": "win", "winner": "bob"}),
        ("halfmove_count", 99),
    ],
)
def test_snapshot_corruption_cannot_replace_replayed_authority(field, value):
    game = session()
    game.submit("alice", 0, "one", Move((5, 0), (4, 1)), 2000)
    corrupt = deepcopy(game.get_state())
    corrupt[field] = value
    with pytest.raises(TransitionError):
        GameManager.from_snapshot(corrupt)


def test_configured_result_blocks_new_moves_but_preserves_exact_retry():
    game = session(outcome=True)
    move = Move((5, 0), (4, 1))
    event = game.submit("alice", 0, "terminal", move, 2000)
    state = game.get_state()
    assert state["outcome"] == {
        "kind": "win",
        "cause": "configured-objective",
        "winner": "alice",
        "priority": 10,
    }
    assert game.get_valid_moves() == []
    assert game.submit("alice", 0, "terminal", move, 200000) == event
    with pytest.raises(TransitionError):
        game.submit("bob", 1, "after-end", Move((0, 5), (1, 4)), 3000)
    assert game.get_state() == state
