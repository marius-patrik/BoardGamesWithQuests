"""Independently exercise FR-61/FR-80 foundation isolation and rejection contracts."""

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import pytest

from engine.model.game.conditions import ConditionEvaluator, QueryResolutionError
from engine.model.game.configuration import (
    ConfigurationError,
    board_from_definition,
    parse_definition_json,
    validate_definition,
)
from engine.model.game.hooks import HookInterpreter
from engine.model.game.snapshot_queries import SnapshotQueries

ROOT = Path(__file__).resolve().parents[1]


def configuration() -> dict[str, Any]:
    """Load genuine game data through an independent caller-owned JSON buffer."""
    return json.loads((ROOT / "packages/chess/config.json").read_text("utf-8"))


def json_value(value: Any) -> Any:
    """Normalize read-only JSON containers for consumer-level value assertions."""
    if isinstance(value, Mapping):
        return {key: json_value(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(child) for child in value]
    return value


def try_replace(container: Any, key: Any, value: Any) -> None:
    """Attempt client mutation, allowing rejection or a detached returned copy."""
    try:
        container[key] = value
    except (TypeError, AttributeError):
        pass


def state_rule(value: Any) -> dict[str, Any]:
    """Describe an actual generic effect with bounded nested JSON state."""
    return {
        "id": "capture_chain",
        "hook": "on_move_made",
        "when": {"op": "true"},
        "effects": [{"op": "set_state", "params": {"name": "chain", "value": value}}],
    }


def test_valid_definition_is_detached_from_original_editor_data() -> None:
    """FR-80: accepted board, piece and clock values survive editor mutation."""
    data = configuration()
    definition = validate_definition(data)
    data["board"]["rows"] = 1
    data["board"]["starting_pieces"][0]["squares"][0][0] = 7
    data["pieces"]["rook"]["moves"][0][0] = 99
    data["clock"]["initial_seconds"] = 0
    assert definition.board["rows"] == 8
    assert json_value(definition.board["starting_pieces"][0]["squares"][0]) == [0, 0]
    assert (
        json_value(definition.pieces["rook"]["moves"]) == configuration()["pieces"]["rook"]["moves"]
    )
    assert definition.clock["initial_seconds"] == configuration()["clock"]["initial_seconds"]
    board = board_from_definition(definition)
    assert board.rows == 8 and board.get_piece_at((0, 0)).getType() == "rook"


def test_returned_definition_data_cannot_change_authoritative_definition() -> None:
    """FR-80: exposed nested containers cannot rewrite a validated position."""
    definition = parse_definition_json(json.dumps(configuration()))
    try_replace(definition.board, "rows", 1)
    try_replace(definition.board["starting_pieces"][0]["squares"][0], 0, 7)
    try_replace(definition.pieces["rook"]["symbols"], "white", "malicious")
    assert definition.board["rows"] == 8
    assert json_value(definition.board["starting_pieces"][0]["squares"][0]) == [0, 0]
    assert (
        definition.pieces["rook"]["symbols"]["white"]
        == configuration()["pieces"]["rook"]["symbols"]["white"]
    )


def test_nested_effect_plan_cannot_be_rewritten_by_rule_author_or_consumer() -> None:
    """FR-61/FR-80: authorized effect data is detached at both trust boundaries."""
    rules = [state_rule({"landings": [[3, 4]], "enabled": True})]
    interpreter = HookInterpreter(rules, {})
    rules[0]["effects"][0]["params"]["value"]["landings"][0][0] = 99
    evaluation = interpreter.evaluate("on_move_made")
    params = evaluation.effects[0].params
    assert json_value(params["value"]) == {"landings": [[3, 4]], "enabled": True}
    try_replace(params["value"]["landings"][0], 0, 99)
    assert json_value(params["value"]) == {"landings": [[3, 4]], "enabled": True}
    assert json_value(interpreter.evaluate("on_move_made").effects[0].params) == json_value(params)


@pytest.mark.parametrize("depth", [100, 1200])
def test_hostile_json_nesting_is_a_configuration_error(depth: int) -> None:
    """FR-80: complexity and decoder recursion failures use the public error."""
    data = configuration()
    data["rules"] = [state_rule("DEPTH_SENTINEL")]
    raw = json.dumps(data).replace('"DEPTH_SENTINEL"', "[" * depth + "0" + "]" * depth)
    with pytest.raises(ConfigurationError):
        parse_definition_json(raw)


@pytest.mark.parametrize("surface", ["piece", "symbols", "board", "placement", "clock"])
def test_unknown_nested_configuration_fields_are_rejected(surface: str) -> None:
    """FR-80: executable or misspelled nested extensions cannot enter snapshots."""
    data = configuration()
    targets = {
        "piece": data["pieces"]["rook"],
        "symbols": data["pieces"]["rook"]["symbols"],
        "board": data["board"],
        "placement": data["board"]["starting_pieces"][0],
        "clock": data["clock"],
    }
    targets[surface]["python_rules"] = "import os"
    with pytest.raises(ConfigurationError):
        parse_definition_json(json.dumps(data))


@pytest.mark.parametrize(
    "operation,params",
    [
        ("move_piece", {}),
        ("move_piece", {"start": [True, 2], "end": [3, 4]}),
        ("move_piece", {"start": [5, 2], "end": [3, 4], "bypass": True}),
        ("set_state", {"name": "", "value": 1}),
        ("propose_outcome", {"kind": "win", "cause": "test", "winner": True, "priority": 1}),
    ],
)
def test_malformed_effect_arguments_cannot_be_planned(operation: str, params: dict) -> None:
    """FR-61: whitelisted operation names do not authorize malformed arguments."""
    rule = state_rule(1)
    rule["effects"] = [{"op": operation, "params": params}]
    with pytest.raises(ValueError):
        HookInterpreter([rule], {}).evaluate("on_move_made")


def test_reference_resolving_to_invalid_effect_argument_fails_closed() -> None:
    """FR-61: typed references must satisfy the resolved operation contract."""
    rule = state_rule(1)
    rule["effects"] = [
        {"op": "move_piece", "params": {"start": {"ref": "move.start"}, "end": [3, 4]}}
    ]
    with pytest.raises(ValueError):
        HookInterpreter([rule], {}, {"move.start": [True, 2]}).evaluate("on_move_made")


def route() -> dict:
    """Describe one genuine enumerator-shaped diagonal capture path."""
    return {"start": [5, 2], "steps": [{"landing": [3, 4], "captured": [4, 3]}]}


def test_capture_queries_distinguish_active_and_opponent() -> None:
    """FR-61: another participant's paths cannot create mandatory captures."""
    queries = SnapshotQueries({"capture_paths": {"active": [route()], "opponent": []}})
    assert queries.capture_paths({"side": "active"}) is True
    assert queries.capture_paths({"side": "opponent"}) is False
    assert queries.capture_count({"scope": "maximum"}) == 1
    reverse = SnapshotQueries({"capture_paths": {"active": [], "opponent": [route()]}})
    assert reverse.capture_paths({"side": "active"}) is False
    assert reverse.capture_paths({"side": "opponent"}) is True
    assert reverse.capture_count({"scope": "maximum"}) == 0


def test_capture_query_rejects_invalid_participant_selector() -> None:
    """FR-80: unknown identity cannot silently select either participant."""
    queries = SnapshotQueries({"capture_paths": {"active": [route()], "opponent": []}})
    with pytest.raises(QueryResolutionError):
        queries.capture_paths({"side": "spectator"})


@pytest.mark.parametrize(
    "left,right",
    [([True], [1]), ([[False]], [[0]]), ([{"enabled": True}], [{"enabled": 1}])],
)
def test_recursive_equality_never_coerces_booleans_into_numbers(left: Any, right: Any) -> None:
    """FR-61: deeply nested JSON comparisons preserve authored value types."""
    evaluator = ConditionEvaluator({})
    expression = {"op": "compare", "relation": "eq", "left": left, "right": right}
    assert evaluator.evaluate(expression) is False
    expression["relation"] = "ne"
    assert evaluator.evaluate(expression) is True
    expression.update(relation="eq", right=left)
    assert evaluator.evaluate(expression) is True


@pytest.mark.parametrize(
    "left,right", [(True, [1]), ([True], [[1]]), ([{"v": True}], [[{"v": 1}]])]
)
def test_membership_never_coerces_nested_booleans_into_numbers(left: Any, right: Any) -> None:
    """FR-61: allowed-value membership uses the same strict JSON comparison."""
    evaluator = ConditionEvaluator({})
    expression = {"op": "compare", "relation": "in", "left": left, "right": right}
    assert evaluator.evaluate(expression) is False
    expression["right"] = [left]
    assert evaluator.evaluate(expression) is True
