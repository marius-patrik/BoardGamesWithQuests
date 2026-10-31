"""Observable declarative-rule and local-session regressions for equality metering."""

from __future__ import annotations

import pytest

from model.capture_policy import EvaluationBudget, EvaluationBudgetExceeded
from model.hooks import RuleProgram
from model.session import DesktopSession


def _run_comparison(relation, left, right, *, limit=100_000):
    """Execute a validated JSON hook with trusted context and a real work budget."""
    program = RuleProgram(
        [
            {
                "id": "equality-test",
                "hook": "on_move_made",
                "when": {
                    "op": "compare",
                    "relation": relation,
                    "left": {"ref": "rule.left"},
                    "right": {"ref": "rule.right"},
                },
                "effects": [],
            }
        ]
    )
    budget = EvaluationBudget(limit)
    result = program.evaluate(
        "on_move_made",
        {},
        {"rule.left": left, "rule.right": right},
        work=budget.consume,
    )
    return bool(result.matched_rule_ids)


@pytest.mark.parametrize("relation", ["eq", "ne", "in"])
def test_declarative_equality_and_list_membership_exhaust_aggregate_budget(relation):
    """A resolved reference must not make recursive comparison work unmetered."""
    target = list(range(48))
    right = [target] if relation == "in" else target
    # Rule dispatch and reference lookup cost only four units before the fix.
    # Comparing 48 array elements must require additional reserved work.
    with pytest.raises(EvaluationBudgetExceeded, match="aggregate evaluation work"):
        _run_comparison(relation, target, right, limit=20)


@pytest.mark.parametrize(
    ("relation", "left", "right", "expected"),
    [
        ("eq", True, 1, False),
        ("ne", False, 0, True),
        ("eq", 1, 1.0, False),
        ("eq", [True, {"x": [1, None]}], [1, {"x": [1, None]}], False),
        ("eq", [{"left": [1, {"x": False}]}], [{"left": [1, {"x": False}]}], True),
        ("eq", [{"a": [1, 2], "b": None}], [{"b": None, "a": [1, 2]}], True),
        ("ne", [{"a": [1, 2]}], [{"a": [1, 3]}], True),
        ("in", [True], [[1], [True]], True),
        ("in", [True], [[1]], False),
        ("in", "needle", "haystack-needle", True),
        ("in", "a", {"a": 1}, True),
    ],
)
def test_declarative_json_equality_is_type_strict_and_nested(relation, left, right, expected):
    assert _run_comparison(relation, left, right) is expected


def test_nested_membership_charges_each_candidate_until_match():
    needle = [{"branches": [1, {"active": True}, None]}]
    haystack = [
        [{"branches": [1, {"active": 1}, None]}],
        [{"branches": [1, {"active": False}, None]}],
        needle,
    ]
    assert _run_comparison("in", needle, haystack)
    with pytest.raises(EvaluationBudgetExceeded, match="aggregate evaluation work"):
        _run_comparison("in", needle, haystack, limit=15)


@pytest.mark.parametrize(
    "game,actor,start,hops",
    [
        ("chess", "white", [6, 4], [[5, 4]]),
        ("checkers", "black", [2, 3], [[3, 2]]),
    ],
)
def test_rejected_budgeted_game_action_is_atomic(monkeypatch, game, actor, start, hops):
    """Exhausting the real authoritative operation cannot commit an event or clock."""
    from model import manager as manager_module

    session = DesktopSession(game)
    legal = next(
        action
        for action in session.legal_actions()
        if action["start"] == start and action["hops"] == hops
    )
    before = session.snapshot()
    monkeypatch.setattr(manager_module, "MAX_EVALUATION_WORK", 1)
    with pytest.raises(EvaluationBudgetExceeded, match="aggregate evaluation work"):
        session.submit(
            actor, before["revision"], {"type": "move", "move": legal}, action_id="budget"
        )
    assert session.snapshot() == before
    assert session.snapshot()["events"] == []
