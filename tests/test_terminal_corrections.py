"""FR-11/50/69: review defects in projected arbitration and timeout identity."""

from copy import deepcopy
import json

import pytest

from engine.model.game.capture_geometry import EvaluationBudget, EvaluationBudgetExceeded
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move
from test_terminal_actions import (
    compare,
    configuration,
    game,
    outcome_rule,
    query,
    ref,
    target_config,
)


def projected_data(priority):
    data = configuration()
    data["quests"] = [
        {"id": "objective", "description": "Move", "when": {"op": "true"}, "reward": 5}
    ]
    decisive = outcome_rule("move-win", {"op": "true"}, "win", 1, priority)
    decisive["hook"] = "on_move_made"
    data["rules"].extend(
        [
            decisive,
            outcome_rule("claim", compare(ref("event.type"), "claim_draw"), priority=10),
        ]
    )
    return data


def claim(intended=True):
    return {
        "type": "claim_draw",
        "claim": "claim",
        "intended_move": Move((0, 0), (0, 1)).to_json() if intended else None,
    }


def test_projected_decisive_proposal_denies_claim_atomically_and_move_still_wins():
    session = game(projected_data(100))
    before = session.get_state()
    with pytest.raises(TransitionError, match="decisive"):
        session.submit_action("alice", 0, "action", claim(), 1)
    assert session.get_state() == before
    event = session.submit_action(
        "alice",
        0,
        "action",
        {
            "type": "move",
            "move": claim()["intended_move"],
        },
        1,
    )
    assert event["outcome"]["winner"] == "alice"
    assert GameManager.from_snapshot(session.get_state()).get_state() == session.get_state()


def test_lower_priority_projected_proposal_allows_draw_without_publishing_projection():
    session = game(projected_data(1))
    before = session.get_state()
    event = session.submit_action("alice", 0, "claim", claim(), 1)
    after = session.get_state()
    assert event["outcome"]["kind"] == "draw"
    assert event["effects"] == [] and event["captured"] == [] and event["move"] is None
    for field in ("board", "quest_progress", "position_history", "halfmove_count", "active_side"):
        assert after[field] == before[field]
    assert after["clocks"]["remaining_ms"]["1"] == 599999
    assert GameManager.from_snapshot(after).get_state() == after
    forged = deepcopy(after)
    forged["config"]["rules"][1]["effects"][0]["params"]["priority"] = 100
    with pytest.raises(TransitionError):
        GameManager.from_snapshot(forged)


def test_null_intended_move_does_not_invent_projected_proposals():
    session = game(projected_data(100))
    event = session.submit_action("alice", 0, "claim", claim(False), 1)
    assert event["outcome"]["kind"] == "draw"
    after = session.get_state()
    assert session.submit_action("alice", 0, "claim", claim(False), 999) == event
    assert GameManager.from_snapshot(after).get_state() == after


def timeout_data(*, pinned=False, initial=1, denied=False):
    data = target_config(pinned)
    data["clock"] = {"initial_seconds": initial, "increment_seconds": 0}
    if denied:
        data["rules"].append(
            {
                "id": "deny",
                "hook": "permits_move",
                "when": {"op": "true"},
                "effects": [{"op": "deny", "params": {}}],
            }
        )
    data["rules"].append(
        outcome_rule(
            "timeout-repeat",
            {
                "op": "all",
                "args": [
                    compare(ref("event.type"), "timeout"),
                    compare(query("repetition_count", scope="position"), 1),
                ],
            },
        )
    )
    return data


@pytest.mark.parametrize("at_ms", [1000, 1001])
def test_timeout_repetition_keeps_legal_capture_target_and_position_key(at_ms):
    session = game(timeout_data())
    before = session.get_state()
    key = before["position_history"][0]
    assert json.loads(key)["targets"]["passing"] == [2, 3]
    with pytest.raises(TransitionError):
        session.submit_action(
            "alice",
            0,
            "late",
            {
                "type": "move",
                "move": Move((3, 2), (2, 3)).to_json(),
            },
            at_ms,
        )
    assert session.get_state() == before
    event = session.submit_action("bob", 0, "timeout", {"type": "timeout"}, at_ms)
    after = session.get_state()
    assert event["outcome"]["kind"] == "draw"
    assert after["clocks"]["remaining_ms"]["1"] == 0
    assert session._position_key(after) == key
    for field in ("board", "quest_progress", "temporary_targets", "position_history"):
        assert after[field] == before[field]
    assert GameManager.from_snapshot(after).get_state() == after


def test_zero_initial_clock_keeps_capture_identity_but_cannot_authorize_move():
    session = game(timeout_data(initial=0))
    before = session.get_state()
    key = before["position_history"][0]
    assert json.loads(key)["targets"]["passing"] == [2, 3]
    assert session.get_valid_moves() == []
    session.submit_action("alice", 0, "timeout", {"type": "timeout"}, 0)
    assert session._position_key(session.get_state()) == key
    assert GameManager.from_snapshot(session.get_state()).get_state() == session.get_state()


@pytest.mark.parametrize(
    "pinned,denied,no_capture", [(True, False, False), (False, True, False), (False, False, True)]
)
def test_expired_identity_still_requires_capture_safety_and_authorization(
    pinned, denied, no_capture
):
    data = timeout_data(pinned=pinned, denied=denied)
    if no_capture:
        data["rules"][1]["effects"][0]["params"]["effects"] = []
    session = game(data)
    key = session.get_state()["position_history"][0]
    assert json.loads(key)["targets"]["passing"] is None
    session.submit_action("bob", 0, "timeout", {"type": "timeout"}, 1000)
    after = session.get_state()
    assert session._position_key(after) == key
    assert GameManager.from_snapshot(after).get_state() == after


def test_expired_capture_probe_uses_shared_operation_budget_and_rolls_back():
    session = game(timeout_data())
    before = session.get_state()
    budget = EvaluationBudget(1000000)
    with session._lock, session._operation(budget):
        session.submit_action("bob", 0, "timeout", {"type": "timeout"}, 1000)
    required = budget.used
    session = game(timeout_data())
    budget = EvaluationBudget(required - 1)
    with pytest.raises(EvaluationBudgetExceeded):
        with session._lock, session._operation(budget):
            session.submit_action("bob", 0, "timeout", {"type": "timeout"}, 1000)
    assert session.get_state() == before
