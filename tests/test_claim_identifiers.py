"""Configured outcome-rule identifiers retain their declarative name contract."""

import pytest

from engine.model.game.configuration import MAX_GAME_JSON_BYTES
from engine.model.game.manager import TransitionError
from test_terminal_actions import configuration, game, outcome_rule, compare, ref


@pytest.mark.parametrize("length", [128, 129, 1024, 1025, 4096])
def test_claim_can_select_a_valid_configured_rule_beyond_session_id_limits(length):
    data = configuration()
    rule = outcome_rule("draw_claim", compare(ref("event.type"), "claim_draw"))
    rule["id"] = "r" * length
    data["rules"].append(rule)
    session = game(data)
    request = {"type": "claim_draw", "claim": rule["id"], "intended_move": None}
    event = session.submit_action("alice", 0, "claim", request, 1)
    saved = session.get_state()
    assert event["outcome"]["kind"] == "draw"
    assert event["action"]["claim"] == rule["id"]
    recovered = type(session).from_snapshot(saved)
    assert recovered.get_state() == saved
    assert recovered.submit_action("alice", 0, "claim", request, 1000) == event
    assert recovered.get_state() == saved


@pytest.mark.parametrize("claim", ["", None, True, [], "x" * (MAX_GAME_JSON_BYTES + 1)])
def test_malformed_or_overbounded_claim_rejects_without_state_changes(claim):
    session = game()
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit_action(
            "alice", 0, "invalid", {"type": "claim_draw", "claim": claim, "intended_move": None}, 1
        )
    assert session.get_state() == before


@pytest.mark.parametrize(
    "identifier", ["棋" * 4096, "r" * 65536, "__import__('os').system('false')"]
)
def test_claim_identifiers_are_exact_inert_configuration_data(identifier):
    """FR-68/69: long or code-shaped IDs select data, never executable names."""
    data = configuration()
    rule = outcome_rule("draw_claim", compare(ref("event.type"), "claim_draw"))
    rule["id"] = identifier
    data["rules"].append(rule)
    session = game(data)
    before = session.get_state()
    for claim in (identifier + "x", identifier.upper() + "x"):
        with pytest.raises(TransitionError):
            session.submit_action(
                "alice",
                0,
                "claim",
                {"type": "claim_draw", "claim": claim, "intended_move": None},
                1,
            )
        assert session.get_state() == before
    event = session.submit_action(
        "alice", 0, "claim", {"type": "claim_draw", "claim": identifier, "intended_move": None}, 1
    )
    assert event["action"]["claim"] == identifier
    assert event["outcome"]["kind"] == "draw"
    assert type(session).from_snapshot(session.get_state()).get_state() == session.get_state()


@pytest.mark.parametrize("claim", ["😀" * (MAX_GAME_JSON_BYTES // 4 + 1), "\ud800"])
def test_claim_utf8_byte_overflow_and_invalid_unicode_reject_atomically(claim):
    """FR-69: the claim exception retains its byte bound and safe encoding failure."""
    session = game()
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit_action(
            "alice", 0, "claim", {"type": "claim_draw", "claim": claim, "intended_move": None}, 1
        )
    assert session.get_state() == before


def test_claim_reference_byte_ceiling_does_not_relax_other_reference_bounds():
    """FR-69: only claim IDs may exceed ordinary expression string limits."""
    from engine.model.game.conditions import ConditionEvaluator

    at_limit = "😀" * (MAX_GAME_JSON_BYTES // 4)
    evaluator = ConditionEvaluator({}, {"event.claim": at_limit})
    assert evaluator.resolve({"ref": "event.claim"}) == at_limit
    with pytest.raises(ValueError):
        ConditionEvaluator({}, {"event.claim": at_limit + "x"})
    with pytest.raises(ValueError):
        ConditionEvaluator({}, {"event.actor": "x" * 1025})
