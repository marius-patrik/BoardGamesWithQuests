"""Behavioral foundation tests for bounded declarative game rules.

These tests establish only the trusted JSON evaluator; actual game transitions
and player-visible acceptance remain separately required.
"""

from __future__ import annotations

import pytest

from model.game.conditions import ConditionEvaluator, QueryResolutionError
from model.game.hooks import RuleProgram
from model.game.schema import freeze_json, thaw_json


def rule(when=None, *, operation="permit"):
    return {
        "id": "rule-1",
        "hook": "permits_move",
        "when": when if when is not None else {"op": "true"},
        "effects": [{"op": operation, "params": {}}],
    }


def test_json_program_proposes_one_permit_without_executing_effects():
    original = rule()
    program = RuleProgram([original])
    original["effects"][0]["op"] = "deny"
    result = program.evaluate("permits_move", {})
    assert result.matched_rule_ids == ("rule-1",)
    assert len(result.effects) == 1
    assert result.effects[0].op == "permit"
    assert dict(result.effects[0].params) == {}


def test_unknown_executable_effect_is_rejected_at_definition_boundary():
    with pytest.raises(ValueError):
        RuleProgram([rule(operation="exec")])


def test_unregistered_json_query_is_not_executable():
    with pytest.raises((ValueError, QueryResolutionError)):
        ConditionEvaluator({"__import__": lambda _: True})


def test_json_snapshot_is_detached_and_nested_data_is_immutable():
    input_value = {"board": [{"piece": "king", "square": [7, 4]}]}
    frozen = freeze_json(input_value)
    input_value["board"][0]["square"][0] = 0
    assert thaw_json(frozen)["board"][0]["square"] == [7, 4]
    modified = thaw_json(frozen)
    modified["board"][0]["square"][0] = 0
    assert thaw_json(frozen)["board"][0]["square"] == [7, 4]
    with pytest.raises(TypeError):
        frozen["board"] = []


def test_unbound_reference_raises_without_python_execution():
    evaluator = ConditionEvaluator({}, {})
    with pytest.raises(QueryResolutionError):
        evaluator.resolve({"ref": "player.id"})
