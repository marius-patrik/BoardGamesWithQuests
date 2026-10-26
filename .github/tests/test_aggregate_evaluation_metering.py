"""Authoritative JSON predicate metering and late-candidate rollback acceptance.

Runs the real GameManager with schema-validated variants of the bundled
Chess/English-Draughts definitions and actual operation-scoped budgets.
No evaluator, query, clock, or transition implementation is mocked.
"""

from __future__ import annotations

import json
from importlib import resources

import pytest

from model.game.capture_policy import EvaluationBudget, EvaluationBudgetExceeded, MAX_EVALUATION_WORK
from model.game.definition import validate_definition
from model.game.manager import GameManager, TransitionError
from model.game.move import Move


def _predicate(expensive: bool) -> dict:
    """Both predicates are true and have equal static JSON size.

    Only the number of dynamically compared elements differs. The cheap
    predicate short-circuits at the first mismatched element; the expensive
    predicate traverses all 72 elements. This distinguishes actual metering
    from static _json_work charges or normal game outcome differences.
    """
    left = list(range(72))
    right = left.copy()
    if not expensive:
        right[0] = -1
    return {
        "op": "compare",
        "relation": "eq" if expensive else "ne",
        "left": left,
        "right": right,
    }


def _manager(game: str, stage: str, expensive: bool) -> GameManager:
    data = json.loads(
        resources.files("games").joinpath(game, "config.json").read_text(encoding="utf-8")
    )
    data["name"] = "metering-" + game
    data["title"] = "Metering reference session"
    data["default"] = False
    # Keep real bundled boards, piece geometry, clocks, and public validators.
    # Remove unrelated outcome/quest behavior to attribute a budget delta to
    # precisely one configured predicate evaluation path.
    data["rules"] = [
        {
            "id": "authorize-movement",
            "hook": "permits_move",
            "when": {"op": "true"},
            "effects": [{"op": "permit", "params": {}}],
        }
    ]
    data["quests"] = []
    data.pop("halfmove_reset", None)
    data.pop("position_identity", None)
    if stage == "halfmove":
        data["halfmove_reset"] = _predicate(expensive)
    elif stage == "quest":
        data["quests"] = [
            {
                "id": "budgeted-quest",
                "description": "Complete a real legal move",
                "when": _predicate(expensive),
                "reward": 7,
            }
        ]
    elif stage == "draw":
        data["rules"].append(
            {
                "id": "budgeted-draw",
                "hook": "outcome",
                "when": _predicate(expensive),
                "effects": [
                    {
                        "op": "propose_outcome",
                        "params": {
                            "kind": "draw",
                            "cause": "budgeted-draw",
                            "winner": None,
                            "priority": 10,
                        },
                    }
                ],
            }
        )
    else:
        raise AssertionError("unknown metering stage")
    return GameManager(validate_definition(data), "budget-case", ("white", "black"), 0)


def _request(state: dict, game: str, stage: str) -> dict:
    if stage == "draw":
        return {"type": "claim_draw", "claim": "budgeted-draw", "intended_move": None}
    move = (
        Move((6, 4), (5, 4))
        if game == "chess"
        else Move((2, 3), (3, 2))
    )
    return {"type": "move", "move": move.to_json()}


def _execute(manager: GameManager, game: str, stage: str, limit: int):
    state = manager.get_state()
    actor = state["participants"][str(state["active_side"])]
    budget = EvaluationBudget(limit)
    with manager._operation(budget):
        result = manager.submit_action(
            actor, state["revision"], "metered-action", _request(state, game, stage), 1
        )
    return budget.used, result


@pytest.mark.parametrize("game", ["chess", "checkers"])
@pytest.mark.parametrize("stage", ["halfmove", "quest", "draw"])
def test_actual_evaluation_work_is_bounded_and_rejected_atomically(game, stage):
    """Dynamic predicate cost, not static configuration size, must determine admission."""
    cheap = _manager(game, stage, expensive=False)
    cheap_before = cheap.get_state()
    cheap_used, cheap_event = _execute(cheap, game, stage, MAX_EVALUATION_WORK)
    assert cheap_used < MAX_EVALUATION_WORK - 32
    assert cheap_event["revision"] == 1
    assert cheap.get_state()["revision"] == 1

    expensive = _manager(game, stage, expensive=True)
    before = expensive.get_state()
    # The cheap and expensive definitions have identical JSON shape/length
    # and produce the SAME successful result. Only the equality traversal
    # differs, so the aggregate ceiling must reject the additional work.
    with pytest.raises(EvaluationBudgetExceeded, match="aggregate evaluation work"):
        _execute(expensive, game, stage, cheap_used + 16)
    after = expensive.get_state()
    assert after == before
    for key in (
        "board",
        "revision",
        "events",
        "clocks",
        "halfmove_count",
        "quest_progress",
        "quest_scores",
        "outcome",
        "position_history",
        "captured",
    ):
        assert after[key] == before[key], key
    assert GameManager.from_snapshot(after).get_state() == before

    # A fully funded operation must still complete the same gameplay,
    # clock, quest reward or claim and be safe to retry and replay.
    spent, event = _execute(expensive, game, stage, MAX_EVALUATION_WORK)
    assert spent > cheap_used + 16
    accepted = expensive.get_state()
    assert accepted["revision"] == len(accepted["events"]) == 1
    assert event == expensive.submit_action(
        accepted["events"][0]["actor"],
        0,
        "metered-action",
        _request(before, game, stage),
        999,
    )
    assert expensive.get_state() == accepted
    assert GameManager.from_snapshot(accepted).get_state() == accepted
    if stage == "halfmove":
        assert accepted["halfmove_count"] == 0
        assert accepted["board"] != before["board"]
        assert accepted["clocks"]["remaining_ms"] != before["clocks"]["remaining_ms"]
    elif stage == "quest":
        assert accepted["quest_scores"][event["actor"]] == 7
        assert accepted["quest_progress"][event["actor"]]["budgeted-quest"]["completed"]
    else:
        assert accepted["outcome"]["kind"] == "draw"
        assert accepted["outcome"]["cause"] == "budgeted-draw"


def test_ineligible_named_draw_claim_is_rejected_without_side_effects():
    manager = _manager("chess", "draw", expensive=True)
    # Existing terminal rules must reject missing configured claims without
    # applying any reserved work as state mutations.
    original = manager.get_state()
    with pytest.raises(TransitionError, match="name one configured outcome rule"):
        manager.submit_action(
            "white", 0, "wrong-draw", {
                "type": "claim_draw", "claim": "not-a-rule", "intended_move": None
            }, 1
        )
    assert manager.get_state() == original
