"""Deterministic aggregate work budget and rollback-safe counter admission."""

from __future__ import annotations

import pytest

from model.game.capture_policy import EvaluationBudget, EvaluationBudgetExceeded
from model.game.hooks import RuleProgram
from model.game.snapshot_queries import SnapshotQueries


def test_nested_work_reservations_fail_atomically_for_all_counters():
    root = EvaluationBudget(4)
    child = EvaluationBudget(10, parent=root)
    child.consume(3)
    assert root.used == child.used == 3
    with pytest.raises(EvaluationBudgetExceeded):
        child.consume(2)
    assert root.used == child.used == 3


@pytest.mark.parametrize("invalid", [-1, 0, True, 3.2])
def test_work_budget_requires_strict_positive_integer(invalid):
    with pytest.raises(ValueError):
        EvaluationBudget(invalid)


def test_declarative_queries_cannot_evaluate_unbounded_work():
    rule = {
        "id": "read-rule-state",
        "hook": "permits_move",
        "when": {
            "op": "compare",
            "relation": "eq",
            "left": {"query": "rule_state", "params": {"name": "ready"}},
            "right": True,
        },
        "effects": [{"op": "permit", "params": {}}],
    }
    reader = SnapshotQueries({"rule_state": {"ready": True}})
    program = RuleProgram([rule])
    with pytest.raises(EvaluationBudgetExceeded):
        program.evaluate(
            "permits_move",
            {"rule_state": reader.rule_state},
            work=EvaluationBudget(1).consume,
        )
    assert (
        len(
            program.evaluate(
                "permits_move",
                {"rule_state": reader.rule_state},
                work=EvaluationBudget(500).consume,
            ).effects
        )
        == 1
    )
