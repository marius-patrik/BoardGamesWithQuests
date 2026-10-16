"""Adversarial consumer contracts for explicit terminal actions and identities."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json

import pytest

from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move
from test_terminal_actions import (
    configuration,
    game,
    outcome_rule,
    compare,
    ref,
    query,
    identity,
    repeat,
)


def resignation_data(start=-1):
    """Return declarative resignation rules independent of the opening color."""
    data = configuration()
    data["starting_side"] = start
    data["clock"] = {"initial_seconds": 1, "increment_seconds": 7}
    data["rules"].append(
        outcome_rule(
            "resigned", compare(ref("event.type"), "resign"), "win", ref("player.opponent.id")
        )
    )
    return data


@pytest.mark.parametrize("start", [-1, 1])
@pytest.mark.parametrize("actor", ["alice", "bob"])
def test_resignation_charges_running_color_and_retry_preserves_exact_terminal_event(start, actor):
    session = game(resignation_data(start))
    before = session.get_state()
    event = session.submit_action(actor, 0, "terminal", {"type": "resign"}, 250)
    after = session.get_state()
    assert after["clocks"]["remaining_ms"] == {str(start): 750, str(-start): 1000}
    assert event["outcome"]["winner"] == ("bob" if actor == "alice" else "alice")
    assert set(event) == {
        "revision",
        "expected_revision",
        "actor",
        "action_id",
        "at_ms",
        "move",
        "captured",
        "effects",
        "outcome",
        "action",
    }
    for key in ("board", "active_side", "quest_progress", "position_history", "halfmove_count"):
        assert after[key] == before[key]
    event["action"]["type"] = "timeout"
    saved = after["events"][0]
    recovered = GameManager.from_snapshot(after)
    assert recovered.submit_action(actor, 0, "terminal", {"type": "resign"}, 9000) == saved
    assert recovered.get_state() == after
    for who, revision, dto in (
        (actor, 1, {"type": "resign"}),
        ("bob" if actor == "alice" else "alice", 0, {"type": "resign"}),
        (actor, 0, {"type": "timeout"}),
    ):
        with pytest.raises(TransitionError):
            recovered.submit_action(who, revision, "terminal", dto, 9010)
        assert recovered.get_state() == after


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        {"type": "resign", "at_ms": 0},
        {"type": "timeout", "expired_side": 1},
        {"type": "claim_draw", "claim": "x"},
        {"type": "claim_draw", "claim": True, "intended_move": None},
        {"type": "move", "move": {"start": [True, 0], "end": [0, 1], "hops": []}},
        {"type": "unknown"},
    ],
)
def test_malformed_terminal_intents_leave_all_persisted_facts_unchanged(bad):
    session = game(resignation_data())
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit_action("alice", 0, "bad", bad, 1)
    assert session.get_state() == before


@pytest.mark.parametrize("start", [-1, 1])
def test_timeout_expired_side_is_authoritative_opening_color_not_reporting_actor(start):
    data = resignation_data(start)
    data["rules"].append(
        outcome_rule(
            "expired",
            compare(ref("event.type"), "timeout"),
            "win",
            query("integer", operation="subtract", left=0, right=ref("event.expired_side")),
        )
    )
    session = game(data)
    before = session.get_state()
    for actor, revision, now in (
        ("outsider", 0, 1000),
        ("alice", 1, 1000),
        ("bob", 0, 999),
        ("alice", 0, -1),
    ):
        with pytest.raises(TransitionError):
            session.submit_action(actor, revision, "rejected", {"type": "timeout"}, now)
        assert session.get_state() == before
    event = session.submit_action(
        "alice" if start == -1 else "bob", 0, "expired", {"type": "timeout"}, 1000
    )
    assert event["outcome"]["winner"] == ("alice" if start == -1 else "bob")
    assert session.get_state()["clocks"]["remaining_ms"] == {str(start): 0, str(-start): 1000}
    assert GameManager.from_snapshot(session.get_state()).get_state() == session.get_state()


def test_named_claim_rejected_when_higher_decisive_projected_outcome_matches():
    data = configuration()
    data["rules"].extend(
        [
            outcome_rule("claim", compare(ref("event.type"), "claim_draw"), priority=1),
            outcome_rule(
                "decisive", compare(query("halfmove_count"), 1), "win", "alice", priority=10
            ),
        ]
    )
    session = game(data)
    before = session.get_state()
    request = {
        "type": "claim_draw",
        "claim": "claim",
        "intended_move": Move((0, 0), (0, 1)).to_json(),
    }
    with pytest.raises(TransitionError):
        session.submit_action("alice", 0, "claim", request, 100)
    assert session.get_state() == before
    # The rejected projection never consumed its action identifier or changed legality.
    event = session.submit("alice", 0, "claim", Move((0, 0), (0, 1)), 100)
    assert event["outcome"]["winner"] == "alice"


def test_terminal_retry_and_new_terminal_race_publish_only_one_immutable_result():
    session = game(resignation_data())

    def attempt(index):
        try:
            return session.submit_action(
                "alice", 0, "same" if index < 6 else "different", {"type": "resign"}, 10
            )
        except TransitionError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(8)))
    accepted = [result for result in results if result is not None]
    assert accepted and all(event == accepted[0] for event in accepted)
    state = session.get_state()
    assert state["revision"] == 1 and len(state["events"]) == 1
    assert GameManager.from_snapshot(state).get_state() == state


@pytest.mark.parametrize("selected", [False, True])
def test_selected_moved_metadata_alone_controls_returned_position_equivalence(selected):
    data = configuration()
    data["position_identity"] = identity(moved_kinds=["token"] if selected else [])
    session = game(data)
    initial = session.get_state()["position_history"][0]
    repeat(session, 4)
    latest = session.get_state()["position_history"][-1]
    assert (initial == latest) is not selected
    assert GameManager.from_snapshot(session.get_state()).get_state() == session.get_state()


@pytest.mark.parametrize("key", ["action", "outcome"])
def test_corrupted_terminal_history_cannot_be_reconstructed(key):
    session = game(resignation_data())
    session.submit_action("bob", 0, "resign", {"type": "resign"}, 4)
    snapshot = session.get_state()
    corrupt = deepcopy(snapshot)
    if key == "action":
        corrupt["events"][0][key] = {"type": "timeout"}
    else:
        corrupt["events"][0][key]["winner"] = "bob"
    with pytest.raises((TransitionError, ValueError)):
        GameManager.from_snapshot(corrupt)
    assert session.get_state() == snapshot
