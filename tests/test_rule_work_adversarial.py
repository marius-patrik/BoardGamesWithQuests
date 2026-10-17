"""Consumer isolation and authority regressions for immutable rule-program reuse."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from engine.model.game.configuration import ConfigurationError, validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move
from test_terminal_actions import configuration, compare, query, ref, outcome_rule
from test_terminal_corrections import projected_data, claim

FROZEN_CHESS = Path(__file__).parent / "fixtures/chess_budget_reproducer.json"


def make_definition():
    """Build a stateful neutral program with no implicit permission fallback."""
    data = configuration()
    data["initial_state"] = {
        "rule_state": {"enabled": True},
        "special_rights": {"right": True},
        "temporary_targets": {"target": None},
    }
    data["rules"][0]["when"] = {
        "op": "all",
        "args": [
            compare(query("rule_state", name="enabled"), True),
            compare(query("special_rights", name="right"), True),
            compare(query("temporary_target", name="target"), None),
        ],
    }
    data["rules"].append(
        {
            "id": "consume",
            "hook": "on_move_made",
            "when": {"op": "true"},
            "effects": [
                {"op": "set_state", "params": {"name": "enabled", "value": False}},
                {"op": "set_rights", "params": {"name": "right", "value": False}},
                {"op": "set_target", "params": {"name": "target", "value": [1, 1]}},
            ],
        }
    )
    return validate_definition(data)


def test_managers_sharing_definition_never_share_board_rule_values_rights_targets_or_output():
    definition = make_definition()
    first = GameManager(definition, "first", ("alice", "bob"), 0)
    second = GameManager(definition, "second", ("carol", "dave"), 1000)
    untouched = second.get_state()
    assert first.get_valid_moves() == second.get_valid_moves()
    first.submit("alice", 0, "move", Move((0, 0), (0, 1)), 1)
    assert first.get_valid_moves() == []
    assert second.get_state() == untouched
    assert second.get_valid_moves()
    snapshot = first.get_state()
    snapshot["config"]["rules"][0]["effects"][0]["op"] = "deny"
    snapshot["rule_state"]["enabled"] = True
    snapshot["board"].clear()
    assert first.get_state()["board"]
    assert first.get_valid_moves() == []
    assert second.get_state() == untouched
    second.submit("carol", 0, "move", Move((0, 0), (0, 1)), 1001)
    assert second.get_state()["participants"] == {"1": "carol", "-1": "dave"}
    assert first.get_state()["participants"] == {"1": "alice", "-1": "bob"}


def test_shared_program_cannot_cache_actor_reference_from_another_session():
    data = configuration()
    data["rules"][0]["when"] = compare(ref("player.id"), "alice")
    definition = validate_definition(data)
    first = GameManager(definition, "a", ("alice", "bob"), 0)
    second = GameManager(definition, "b", ("carol", "dave"), 0)
    assert first.get_valid_moves()
    assert second.get_valid_moves() == []
    before = second.get_state()
    with pytest.raises(TransitionError):
        second.submit("carol", 0, "same", Move((0, 0), (0, 1)), 1)
    assert second.get_state() == before
    first.submit("alice", 0, "same", Move((0, 0), (0, 1)), 1)
    assert second.get_state() == before


def test_preview_cache_never_bypasses_real_timestamp_deadline_or_other_anchor():
    data = configuration()
    data["clock"] = {"initial_seconds": 1, "increment_seconds": 0}
    definition = validate_definition(data)
    first = GameManager(definition, "first", ("alice", "bob"), 0)
    second = GameManager(definition, "second", ("alice", "bob"), 1000)
    assert first.get_valid_moves() == second.get_valid_moves()
    before = first.get_state()
    with pytest.raises(TransitionError):
        first.submit("alice", 0, "expired", Move((0, 0), (0, 1)), 1000)
    assert first.get_state() == before
    second.submit("alice", 0, "expired", Move((0, 0), (0, 1)), 1001)
    assert second.get_state()["clocks"]["remaining_ms"]["1"] == 999
    assert first.get_state() == before


@pytest.mark.parametrize("priority", [1, 10, 100])
def test_prepared_rule_reuse_preserves_projected_claim_priority_and_nonpublication(priority):
    definition = validate_definition(projected_data(priority))
    first = GameManager(definition, "first", ("alice", "bob"), 0)
    second = GameManager(definition, "second", ("alice", "bob"), 0)
    before = first.get_state()
    other = second.get_state()
    if priority < 10:
        event = first.submit_action("alice", 0, "claim", claim(), 1)
        assert event["outcome"]["kind"] == "draw"
        for field in (
            "board",
            "quest_progress",
            "position_history",
            "active_side",
            "halfmove_count",
        ):
            assert first.get_state()[field] == before[field]
        restored = GameManager.from_snapshot(first.get_state())
        assert restored.submit_action("alice", 0, "claim", claim(), 999) == event
    else:
        with pytest.raises(ValueError):
            first.submit_action("alice", 0, "claim", claim(), 1)
        assert first.get_state() == before
    assert second.get_state() == other
    event = second.submit("alice", 0, "move", Move((0, 0), (0, 1)), 1)
    assert event["outcome"]["kind"] == "win" and event["outcome"]["winner"] == "alice"


@pytest.mark.parametrize(
    "malformation",
    ["unknown-query", "unknown-effect", "duplicate-rule", "unknown-field", "malformed-params"],
)
def test_rule_program_reuse_does_not_authorize_hostile_unvalidated_definitions(malformation):
    data = configuration()
    if malformation == "unknown-query":
        data["rules"][0]["when"] = {"op": "test", "query": "__import__", "params": {}}
    elif malformation == "unknown-effect":
        data["rules"][0]["effects"][0]["op"] = "eval"
    elif malformation == "duplicate-rule":
        data["rules"].append(deepcopy(data["rules"][0]))
    elif malformation == "unknown-field":
        data["rules"][0]["python"] = "return True"
    else:
        data["rules"][0]["effects"] = [
            {"op": "move_piece", "params": {"start": [0, 0], "end": [True, 1]}}
        ]
    with pytest.raises(ConfigurationError):
        validate_definition(data)
    # Failed validation cannot poison the next genuine program/session.
    good = GameManager(validate_definition(configuration()), "valid", ("alice", "bob"), 0)
    assert good.submit("alice", 0, "move", Move((0, 0), (0, 1)), 1)["revision"] == 1


def test_full_frozen_sixty_five_rule_configuration_moves_replays_and_exactly_retries():
    data = json.loads(FROZEN_CHESS.read_text())
    definition = validate_definition(data)
    first = GameManager(definition, "first", ("white", "black"), 0)
    second = GameManager(definition, "second", ("otherwhite", "otherblack"), 0)
    untouched = second.get_state()
    assert len(first.get_valid_moves()) == 20
    before = first.get_state()
    with pytest.raises(TransitionError):
        first.submit("black", 0, "wrong", Move((6, 4), (4, 4)), 1)
    assert first.get_state() == before
    event = first.submit("white", 0, "double", Move((6, 4), (4, 4)), 1)
    first.submit("black", 1, "reply", Move((1, 4), (3, 4)), 2)
    current = first.get_state()
    assert current["revision"] == 2 and current["temporary_targets"]["en_passant"] == [2, 4]
    assert second.get_state() == untouched
    restored = GameManager.from_snapshot(current)
    assert restored.get_state() == current
    assert restored.submit("white", 0, "double", Move((6, 4), (4, 4)), 999) == event
    assert restored.get_state() == current
    with pytest.raises(TransitionError):
        restored.submit("white", 0, "double", Move((6, 3), (4, 3)), 999)
    assert restored.get_state() == current
    assert len(second.get_valid_moves()) == 20


def test_legal_count_result_is_not_reused_for_an_uncommitted_other_manager():
    data = configuration()
    data["initial_state"] = {
        "rule_state": {"enabled": True},
        "special_rights": {},
        "temporary_targets": {},
    }
    data["rules"][0]["when"] = compare(query("rule_state", name="enabled"), True)
    data["rules"].append(
        {
            "id": "disable",
            "hook": "on_move_made",
            "when": {"op": "true"},
            "effects": [{"op": "set_state", "params": {"name": "enabled", "value": False}}],
        }
    )
    data["rules"].append(
        outcome_rule("no-moves", compare(query("legal_move_count", side="active"), 0))
    )
    definition = validate_definition(data)
    first = GameManager(definition, "a", ("alice", "bob"), 0)
    second = GameManager(definition, "b", ("alice", "bob"), 0)
    untouched = second.get_state()
    event = first.submit("alice", 0, "move", Move((0, 0), (0, 1)), 1)
    assert event["outcome"]["kind"] == "draw"
    assert first.get_valid_moves() == []
    assert second.get_state() == untouched and second.get_valid_moves()
    assert second.submit("alice", 0, "move", Move((0, 0), (0, 1)), 1)["outcome"] == event["outcome"]


def test_equivalent_rule_text_never_reuses_projected_safety_of_a_different_board():
    from test_terminal_actions import target_config

    free = GameManager(validate_definition(target_config(False)), "free", ("alice", "bob"), 0)
    pinned = GameManager(validate_definition(target_config(True)), "pinned", ("alice", "bob"), 0)
    move = Move((3, 2), (2, 3))
    original = pinned.get_state()
    assert move in free.get_valid_moves()
    assert move not in pinned.get_valid_moves()
    with pytest.raises(TransitionError):
        pinned.submit("alice", 0, "passing", move, 1)
    assert pinned.get_state() == original
    event = free.submit("alice", 0, "passing", move, 1)
    assert event["captured"] == [[3, 3]]
    assert pinned.get_state() == original
    assert GameManager.from_snapshot(free.get_state()).get_state() == free.get_state()


def test_failed_late_effect_does_not_poison_subsequent_candidate_or_shared_program():
    data = configuration()
    data["board"]["starting_pieces"].append(
        {"piece": "token", "color": "white", "squares": [[0, 2]]}
    )
    data["initial_state"] = {
        "rule_state": {"marker": 0},
        "special_rights": {},
        "temporary_targets": {},
    }
    data["rules"].append(
        {
            "id": "rollback",
            "hook": "on_move_made",
            "when": compare(ref("move.end"), [0, 1]),
            "effects": [
                {"op": "set_state", "params": {"name": "marker", "value": 99}},
                {"op": "capture_piece", "params": {"square": [1, 1]}},
            ],
        }
    )
    definition = validate_definition(data)
    session = GameManager(definition, "a", ("alice", "bob"), 0)
    before = session.get_state()
    assert Move((0, 0), (0, 1)) not in session.get_valid_moves()
    with pytest.raises(TransitionError):
        session.submit("alice", 0, "reused", Move((0, 0), (0, 1)), 1)
    assert session.get_state() == before
    event = session.submit("alice", 0, "reused", Move((0, 2), (0, 3)), 1)
    assert event["effects"] == [] and session.get_state()["rule_state"]["marker"] == 0
    assert event["revision"] == 1 and len(session.get_state()["events"]) == 1
    assert GameManager.from_snapshot(session.get_state()).get_state() == session.get_state()
