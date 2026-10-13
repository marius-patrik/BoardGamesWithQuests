"""Independent FR-61/FR-80 tests of authoritative transitions and replay."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from engine.model.game.configuration import parse_definition_json
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move

ROOT = Path(__file__).resolve().parents[1]


def rule(identifier: str, hook: str, effects: list[dict]) -> dict:
    """Declare a real trusted-operation plan with an explicit true condition."""
    return {"id": identifier, "hook": hook, "when": {"op": "true"}, "effects": effects}


def definition(effects: list[dict] | None = None, capture: bool = False):
    """Create an explicit game-neutral fixture from validated shipped JSON."""
    package = "english_draughts" if capture else "chess"
    data = json.loads((ROOT / "packages" / package / "config.json").read_text("utf-8"))
    data.update(name="test-game", title="Authority contract", playable=False)
    if capture:
        data["board"]["starting_pieces"] = [
            {"piece": "man", "color": "white", "squares": [[5, 2]]},
            {"piece": "man", "color": "black", "squares": [[4, 3], [2, 5], [0, 7]]},
        ]
    else:
        runner = deepcopy(data["pieces"]["rook"])
        runner.update(
            moves=[[0, 1], [0, -1], [1, 0], [-1, 0]],
            attacks=[[0, 1], [0, -1], [1, 0], [-1, 0]],
            repeat=False,
            color_relative=False,
        )
        data["pieces"] = {"runner": runner}
        data["board"]["starting_pieces"] = [
            {"piece": "runner", "color": "white", "squares": [[4, 1]]},
            {"piece": "runner", "color": "black", "squares": [[1, 4]]},
        ]
    data["clock"] = {"initial_seconds": 30, "increment_seconds": 2}
    data["rules"] = [rule("explicit_authority", "permits_move", [{"op": "permit", "params": {}}])]
    if effects:
        data["rules"].append(rule("after_move", "on_move_made", effects))
    data["quests"] = [
        {"id": "first_move", "description": "Make a move", "when": {"op": "true"}, "reward": 5}
    ]
    return parse_definition_json(json.dumps(data))


def session(effects: list[dict] | None = None, capture: bool = False) -> GameManager:
    """Create a fresh authoritative session with known identities and epoch."""
    return GameManager(definition(effects, capture), "test-session", ("alice", "bob"), 1000)


def accepted_session() -> GameManager:
    """Commit one real action so replay has both history and quest effects."""
    manager = session()
    manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 2000)
    return manager


def test_simultaneous_same_revision_actions_commit_exactly_one_transition() -> None:
    """FR-80: a race cannot publish two moves, rewards or clock deductions."""
    manager = session()

    def submit(index: int) -> Any:
        try:
            return manager.submit(
                "alice", 0, f"race-{index}", Move((4, 1), ((4, 2), (3, 1))[index]), 2000
            )
        except TransitionError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, [0, 1]))
    assert sum(result is not None for result in results) == 1
    state = manager.get_state()
    assert state["revision"] == 1 and len(state["events"]) == 1
    assert state["active_side"] == -1
    assert state["clocks"]["remaining_ms"] == {"1": 31000, "-1": 30000}
    assert state["quest_progress"]["alice"]["first_move"]["completed"] is True
    assert state["quest_progress"]["bob"]["first_move"]["completed"] is False
    assert GameManager.from_snapshot(state).get_state() == state


def test_retry_returns_original_event_without_consuming_clock_or_reward() -> None:
    """FR-80: delayed duplicate delivery has no additional observable effects."""
    manager = accepted_session()
    before = manager.get_state()
    result = manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 99999)
    assert result == before["events"][0]
    assert manager.get_state() == before
    result["move"]["hops"][0][0] = 7
    assert manager.get_state() == before


@pytest.mark.parametrize(
    "actor,revision,action,move,timestamp",
    [
        ("stranger", 0, "denied", Move((4, 1), (4, 2)), 2000),
        ("bob", 0, "denied", Move((4, 1), (4, 2)), 2000),
        ("alice", 1, "denied", Move((4, 1), (4, 2)), 2000),
        ("alice", True, "denied", Move((4, 1), (4, 2)), 2000),
        ("alice", 0, "denied", Move((4, 1), (4, 3)), 2000),
        ("alice", 0, "denied", Move((4, 1), (8, 1)), 2000),
        ("alice", 0, "denied", Move((4, 1), (4, 2)), 999),
        ("alice", 0, "denied", Move((4, 1), (4, 2)), True),
        ("alice", 0, "denied", Move((4, 1), (4, 2)), 31000),
    ],
)
def test_invalid_authority_or_action_preserves_entire_snapshot(
    actor: str, revision: int, action: str, move: Move, timestamp: int
) -> None:
    """FR-80: identity, revision, geometry and clock rejection have no effects."""
    manager = session()
    before = manager.get_state()
    with pytest.raises(TransitionError):
        manager.submit(actor, revision, action, move, timestamp)
    assert manager.get_state() == before
    assert manager.submit("alice", 0, "valid", Move((4, 1), (4, 2)), 2000)["revision"] == 1


def test_late_effect_failure_rolls_back_move_clock_quest_and_rule_state() -> None:
    """FR-80: an earlier valid state effect cannot leak from a failed transition."""
    manager = session(
        [
            {"op": "set_state", "params": {"name": "marker", "value": {"seen": True}}},
            {"op": "capture_piece", "params": {"square": [99, 99]}},
        ]
    )
    before = manager.get_state()
    with pytest.raises(TransitionError):
        manager.submit("alice", 0, "failure", Move((4, 1), (4, 2)), 2000)
    assert manager.get_state() == before
    assert GameManager.from_snapshot(before).get_state() == before


def test_relocation_effect_cannot_silently_erase_an_occupied_destination() -> None:
    """FR-80: relocation cannot replace capture accounting or erase a player piece."""
    manager = session(
        [
            {"op": "move_piece", "params": {"start": [1, 4], "end": [4, 2]}},
        ]
    )
    before = manager.get_state()
    with pytest.raises(TransitionError):
        manager.submit("alice", 0, "overwrite", Move((4, 1), (4, 2)), 2000)
    assert manager.get_state() == before


def test_capture_chain_requires_all_hops_and_removes_exactly_the_captured_pieces() -> None:
    """FR-61: full chains are one authoritative action; partial chains reject."""
    manager = session(capture=True)
    before = manager.get_state()
    with pytest.raises(TransitionError):
        manager.submit("alice", 0, "partial", Move((5, 2), (3, 4)), 2000)
    assert manager.get_state() == before
    event = manager.submit("alice", 0, "complete", Move((5, 2), (1, 6), ((3, 4), (1, 6))), 2000)
    state = manager.get_state()
    assert event["captured"] == [[4, 3], [2, 5]]
    assert {(tuple(piece["square"]), piece["side"]) for piece in state["board"]} == {
        ((1, 6), 1),
        ((0, 7), -1),
    }
    assert len(state["captured"]) == 2 and state["revision"] == 1
    assert state["active_side"] == -1 and state["halfmove_count"] == 0
    assert GameManager.from_snapshot(state).get_state() == state


@pytest.mark.parametrize(
    "path,value",
    [
        (("revision",), 77),
        (("revision",), True),
        (("board", 0, "side"), True),
        (("board", 1, "moved"), 1),
        (("clocks", "remaining_ms", "1"), 31000.0),
        (("clocks", "remaining_ms", "1"), 0),
        (("quest_progress", "alice", "first_move", "completed"), 1),
        (("quest_progress", "alice", "first_move", "active"), True),
        (("events", 0, "expected_revision"), False),
        (("events", 0, "move", "hops", 0, 0), True),
    ],
)
def test_replay_rejects_corruption_including_nested_boolean_numeric_aliases(
    path: tuple, value: Any
) -> None:
    """FR-80: replay equality must preserve JSON types as well as apparent values."""
    manager = accepted_session()
    original = manager.get_state()
    damaged = deepcopy(original)
    target = damaged
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(TransitionError):
        GameManager.from_snapshot(damaged)
    assert manager.get_state() == original


def test_snapshot_and_move_transport_reads_are_detached() -> None:
    """FR-80: consumers cannot edit authoritative state through response objects."""
    manager = accepted_session()
    original = manager.get_state()
    exposed = manager.get_state()
    exposed["board"][0]["square"][0] = 99
    exposed["quest_progress"]["alice"]["first_move"]["completed"] = False
    exposed["config"]["clock"]["initial_seconds"] = 999
    assert manager.get_state() == original
    move = Move((1, 4), (1, 5))
    transport = move.to_json()
    transport["hops"][0][0] = 7
    assert move.end_pos == (1, 5)
    assert Move.from_json(move.to_json()) == move


def test_external_definition_replacement_cannot_change_pinned_session_rules() -> None:
    """FR-80: replacing exposed metadata cannot create a competing authority."""
    manager = session()
    replacement = definition(
        [
            {"op": "set_state", "params": {"name": "unapproved", "value": True}},
        ]
    )
    before = manager.get_state()
    try:
        manager.definition = replacement
    except (AttributeError, TypeError):
        pass
    assert manager.get_state() == before
    manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 2000)
    state = manager.get_state()
    assert "unapproved" not in state["rule_state"]
    assert state["config"] == before["config"]
    assert GameManager.from_snapshot(state).get_state() == state


@pytest.mark.parametrize("side,identity", [(1, "alice"), (-1, "bob")])
def test_side_selected_effects_resolve_to_the_pinned_participant(side: int, identity: str) -> None:
    """FR-61: configured canonical sides target the correct clocks and objectives."""
    data = session(
        [
            {"op": "set_clock", "params": {"player": side, "seconds": 42}},
            {"op": "complete_quest", "params": {"player": side, "quest": "first_move"}},
        ]
    ).get_state()["config"]
    data["quests"][0]["when"] = {"op": "false"}
    manager = GameManager(
        parse_definition_json(json.dumps(data)), "side-effects", ("alice", "bob"), 1000
    )
    manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 2000)
    state = manager.get_state()
    assert state["clocks"]["remaining_ms"][str(side)] == 42000
    assert state["quest_progress"][identity]["first_move"]["completed"] is True
    other = "bob" if identity == "alice" else "alice"
    assert state["quest_progress"][other]["first_move"]["completed"] is False
    assert GameManager.from_snapshot(state).get_state() == state


def test_post_move_hooks_and_quests_observe_committed_revision_history_and_turn() -> None:
    """FR-61: post-action decisions see the action once, with actor-relative refs."""
    data = session().get_state()["config"]
    postcondition = {
        "op": "all",
        "args": [
            {
                "op": "compare",
                "relation": "eq",
                "left": {"query": "history_count", "params": {}},
                "right": 1,
            },
            {"op": "compare", "relation": "eq", "left": {"ref": "game.revision"}, "right": 1},
            {
                "op": "compare",
                "relation": "eq",
                "left": {"query": "turn", "params": {}},
                "right": -1,
            },
            {"op": "compare", "relation": "eq", "left": {"ref": "player.id"}, "right": "alice"},
        ],
    }
    data["quests"][0]["when"] = postcondition
    post_rule = rule(
        "observe_commit",
        "on_move_made",
        [{"op": "set_state", "params": {"name": "observed", "value": True}}],
    )
    post_rule["when"] = postcondition
    data["rules"].append(post_rule)
    manager = GameManager(
        parse_definition_json(json.dumps(data)), "lifecycle", ("alice", "bob"), 1000
    )
    manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 2000)
    state = manager.get_state()
    assert state["rule_state"].get("observed") is True
    assert state["quest_progress"]["alice"]["first_move"]["completed"] is True
    assert state["quest_progress"]["bob"]["first_move"]["completed"] is False
    assert len(state["events"]) == 1
    assert GameManager.from_snapshot(state).get_state() == state


def test_authorization_event_is_preserved_in_the_single_committed_action() -> None:
    """FR-61: accepted authorization metadata is not silently dropped."""
    data = session().get_state()["config"]
    data["rules"][0]["effects"].append(
        {
            "op": "record_event",
            "params": {"name": "authorized", "payload": {"actor": {"ref": "player.id"}}},
        }
    )
    manager = GameManager(
        parse_definition_json(json.dumps(data)), "auth-event", ("alice", "bob"), 1000
    )
    event = manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 2000)
    assert event["effects"] == [{"name": "authorized", "payload": {"actor": "alice"}}]
    state = manager.get_state()
    assert state["events"] == [event] and state["revision"] == 1
    assert GameManager.from_snapshot(state).get_state() == state


def test_legal_enumeration_excludes_transitions_with_failing_late_effects() -> None:
    """FR-61: exposed playable actions must survive the same effect preflight."""
    manager = session(
        [
            {"op": "set_state", "params": {"name": "marker", "value": True}},
            {"op": "capture_piece", "params": {"square": [99, 99]}},
        ]
    )
    before = manager.get_state()
    assert manager.get_valid_moves() == []
    assert manager.get_state() == before
    with pytest.raises(TransitionError):
        manager.submit("alice", 0, "bad-effect", Move((4, 1), (4, 2)), 2000)
    assert manager.get_state() == before


def test_zero_clock_has_no_executable_actions_and_preserves_state() -> None:
    """FR-61: geometric candidates cannot bypass an expired configured clock."""
    data = session().get_state()["config"]
    data["clock"]["initial_seconds"] = 0
    manager = GameManager(
        parse_definition_json(json.dumps(data)), "zero-clock", ("alice", "bob"), 1000
    )
    before = manager.get_state()
    assert manager.get_valid_moves() == []
    with pytest.raises(TransitionError):
        manager.submit("alice", 0, "expired", Move((4, 1), (4, 2)), 1000)
    assert manager.get_state() == before


def test_capture_effect_is_accounted_in_event_state_and_halfmove_counter() -> None:
    """FR-61: a declarative special capture has complete authoritative accounting."""
    manager = session(
        [
            {"op": "capture_piece", "params": {"square": [1, 4]}},
        ]
    )
    event = manager.submit("alice", 0, "special-capture", Move((4, 1), (4, 2)), 2000)
    state = manager.get_state()
    assert event["captured"] == [[1, 4]]
    assert state["captured"] == [{"kind": "runner", "side": -1}]
    assert state["halfmove_count"] == 0
    assert state["board"] == [{"square": [4, 2], "kind": "runner", "side": 1, "moved": True}]
    assert state["events"] == [event]
    assert GameManager.from_snapshot(state).get_state() == state


def test_post_action_quest_repetition_query_sees_the_accepted_position() -> None:
    """FR-61: post-action position queries include the position just committed."""
    data = session().get_state()["config"]
    data["quests"][0]["when"] = {
        "op": "compare",
        "relation": "eq",
        "left": {"query": "repetition_count", "params": {"scope": "position"}},
        "right": 1,
    }
    manager = GameManager(
        parse_definition_json(json.dumps(data)), "position-history", ("alice", "bob"), 1000
    )
    manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 2000)
    state = manager.get_state()
    assert len(state["position_history"]) == 2
    assert state["quest_progress"]["alice"]["first_move"]["completed"] is True
    assert state["quest_progress"]["bob"]["first_move"]["completed"] is False
    assert GameManager.from_snapshot(state).get_state() == state


def test_terminal_result_is_persisted_in_event_and_rejects_further_actions() -> None:
    """FR-61/FR-80: terminal authority survives replay and permits exact retry only."""
    data = session().get_state()["config"]
    data["rules"].append(
        rule(
            "result",
            "outcome",
            [
                {
                    "op": "propose_outcome",
                    "params": {
                        "kind": "draw",
                        "cause": "configured",
                        "winner": None,
                        "priority": 1,
                    },
                }
            ],
        )
    )
    manager = GameManager(
        parse_definition_json(json.dumps(data)), "terminal", ("alice", "bob"), 1000
    )
    event = manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 2000)
    state = manager.get_state()
    assert (
        event["outcome"]
        == state["outcome"]
        == {"kind": "draw", "cause": "configured", "winner": None, "priority": 1}
    )
    assert state["events"] == [event]
    assert manager.get_valid_moves() == []
    with pytest.raises(TransitionError):
        manager.submit("bob", 1, "after-result", Move((1, 4), (1, 5)), 3000)
    assert manager.get_state() == state
    assert manager.submit("alice", 0, "first", Move((4, 1), (4, 2)), 99999) == event
    assert GameManager.from_snapshot(state).get_state() == state
