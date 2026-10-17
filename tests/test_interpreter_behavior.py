"""Test observable declarative rule decisions, effects and outcomes."""

import copy

import pytest

from engine.model.game.conditions import QueryResolutionError
from engine.model.game.hooks import HookInterpreter, PlannedEffect
from engine.model.game.outcomes import resolve_outcome
from engine.model.game.schema import thaw_json


def rule(when: dict, operation: str = "permit") -> dict:
    return {
        "id": "move_rule",
        "hook": "permits_move",
        "when": when,
        "effects": [{"op": operation, "params": {"target": {"ref": "move.end"}}}],
    }


def test_valid_move_reference_produces_effect_without_mutating_inputs() -> None:
    references = {"move.start": [6, 3], "move.end": [5, 4]}
    entry = rule(
        {"op": "compare", "relation": "eq", "left": {"ref": "move.start"}, "right": [6, 3]}
    )
    unchanged = copy.deepcopy(entry)
    effects = HookInterpreter([entry], {}, references).evaluate("permits_move")
    assert effects.matched_rule_ids == ("move_rule",)
    assert len(effects.effects) == 1
    assert thaw_json(effects.effects[0].params) == {"target": [5, 4]}
    assert entry == unchanged and references["move.end"] == [5, 4]


def test_rule_not_matching_candidate_cannot_emit_effect() -> None:
    entry = rule(
        {"op": "compare", "relation": "eq", "left": {"ref": "move.start"}, "right": [0, 0]}
    )
    effects = HookInterpreter([entry], {}, {"move.start": [6, 3], "move.end": [5, 4]}).evaluate(
        "permits_move"
    )
    assert effects.effects == ()


@pytest.mark.parametrize("result", [0, None, [], "string"])
def test_non_boolean_predicate_does_not_authorize_action(result: object) -> None:
    entry = rule({"op": "test", "query": "path_clear", "params": {}})
    with pytest.raises(QueryResolutionError, match="boolean"):
        HookInterpreter(
            [entry], {"path_clear": lambda params: result}, {"move.end": [5, 4]}
        ).evaluate("permits_move")


def test_missing_query_or_unbound_reference_fails_closed() -> None:
    entry = rule({"op": "test", "query": "path_clear", "params": {}})
    with pytest.raises(QueryResolutionError, match="not implemented"):
        HookInterpreter([entry], {}, {"move.end": [5, 4]}).evaluate("permits_move")
    missing = rule(
        {"op": "compare", "relation": "eq", "left": {"ref": "move.start"}, "right": [0, 0]}
    )
    with pytest.raises(QueryResolutionError, match="unbound"):
        HookInterpreter([missing], {}, {"move.end": [5, 4]}).evaluate("permits_move")


def test_conflicting_results_of_equal_priority_are_not_silently_selected() -> None:
    def proposal(kind: str, winner: int | None) -> PlannedEffect:
        return PlannedEffect(
            "propose_outcome", {"kind": kind, "cause": "terminal", "winner": winner, "priority": 4}
        )

    with pytest.raises(QueryResolutionError, match="conflicting"):
        resolve_outcome((proposal("draw", None), proposal("win", 1)))
    decided = resolve_outcome((proposal("draw", None),))
    assert decided is not None and decided.kind == "draw" and decided.winner is None
