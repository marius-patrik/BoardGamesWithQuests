"""FR-11/16/50/63/69: authenticated explicit terminal transitions and normalized history."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json

import pytest

from engine.model.game.conditions import QueryResolutionError
from engine.model.game.configuration import ConfigurationError, validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move


def ref(name):
    return {"ref": name}


def query(query_name, **params):
    return {"query": query_name, "params": params}


def compare(left, right, relation="eq"):
    return {"op": "compare", "relation": relation, "left": left, "right": right}


def outcome_rule(identity, when, kind="draw", winner=None, priority=10):
    return {
        "id": identity,
        "hook": "outcome",
        "when": when,
        "effects": [
            {
                "op": "propose_outcome",
                "params": {"kind": kind, "cause": identity, "winner": winner, "priority": priority},
            }
        ],
    }


def configuration():
    piece = {
        "symbols": {"white": "W", "black": "B"},
        "moves": [[0, 1], [0, -1]],
        "attacks": [[0, 1], [0, -1]],
        "jump": False,
        "repeat": False,
    }
    return {
        "schema_version": 2,
        "name": "terminal-neutral",
        "title": "Terminal neutral",
        "default": False,
        "playable": False,
        "board": {
            "rows": 5,
            "columns": 7,
            "starting_pieces": [
                {"piece": "token", "color": "white", "squares": [[0, 0]]},
                {"piece": "token", "color": "black", "squares": [[4, 0]]},
            ],
        },
        "pieces": {"token": piece},
        "clock": {"initial_seconds": 600, "increment_seconds": 1},
        "exports": [],
        "appearance": {},
        "rules": [
            {
                "id": "permission",
                "hook": "permits_move",
                "when": {"op": "true"},
                "effects": [{"op": "permit", "params": {}}],
            }
        ],
        "quests": [],
    }


def game(data=None):
    return GameManager(
        validate_definition(data or configuration()), "terminal", ("alice", "bob"), 0
    )


def repeat(session, count):
    for revision in range(count):
        row = 0 if revision % 2 == 0 else 4
        column = (revision // 2) % 2
        session.submit(
            "alice" if row == 0 else "bob",
            revision,
            f"move-{revision}",
            Move((row, column), (row, 1 - column)),
            revision + 1,
        )


def identity(**changes):
    return {"moved_kinds": [], "rule_state": [], "rights": [], "targets": [], **changes}


@pytest.mark.parametrize("actor,winner", [("alice", "bob"), ("bob", "alice")])
def test_either_participant_resigns_with_durable_exact_retry_and_no_move_effects(actor, winner):
    data = configuration()
    data["rules"].append(
        outcome_rule(
            "resignation", compare(ref("event.type"), "resign"), "win", ref("player.opponent.id")
        )
    )
    session = game(data)
    before = session.get_state()
    event = session.submit_action(actor, 0, "resign", {"type": "resign"}, 2)
    snapshot = session.get_state()
    assert snapshot["outcome"]["winner"] == winner
    assert event["move"] is None and event["action"] == {"type": "resign"}
    for field in ("board", "active_side", "halfmove_count", "position_history", "quest_progress"):
        assert snapshot[field] == before[field]
    assert snapshot["clocks"]["remaining_ms"]["1"] == 599998
    assert snapshot["clocks"]["remaining_ms"]["-1"] == 600000
    assert session.submit_action(actor, 0, "resign", {"type": "resign"}, 500) == event
    assert session.get_state() == snapshot
    assert GameManager.from_snapshot(snapshot).get_state() == snapshot
    with pytest.raises(TransitionError):
        session.submit_action(actor, 1, "again", {"type": "resign"}, 3)


@pytest.mark.parametrize("actor", ["alice", "bob"])
def test_explicit_timeout_uses_trusted_deadline_and_clamps_once(actor):
    data = configuration()
    data["clock"] = {"initial_seconds": 1, "increment_seconds": 3}
    data["rules"].append(
        outcome_rule(
            "flag",
            compare(ref("event.type"), "timeout"),
            "win",
            query("integer", operation="subtract", left=0, right=ref("event.expired_side")),
        )
    )
    session = game(data)
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit_action(actor, 0, "early", {"type": "timeout"}, 999)
    assert session.get_state() == before
    with pytest.raises(TransitionError):
        session.submit("alice", 0, "expired-move", Move((0, 0), (0, 1)), 1000)
    assert session.get_state() == before
    event = session.submit_action(actor, 0, "flag", {"type": "timeout"}, 1000)
    state = session.get_state()
    assert event["outcome"]["winner"] == "bob"
    assert state["clocks"]["remaining_ms"] == {"1": 0, "-1": 1000}
    assert state["clocks"]["anchor_ms"] == 1000
    assert session.submit_action(actor, 0, "flag", {"type": "timeout"}, 5000) == event
    assert GameManager.from_snapshot(state).get_state() == state


def test_timeout_draw_condition_is_configuration_data():
    data = configuration()
    data["clock"]["initial_seconds"] = 0
    data["initial_state"] = {
        "rule_state": {"can_finish": False},
        "special_rights": {},
        "temporary_targets": {},
    }
    data["rules"].append(
        outcome_rule(
            "no-finish",
            {
                "op": "all",
                "args": [
                    compare(ref("event.type"), "timeout"),
                    compare(query("rule_state", name="can_finish"), False),
                ],
            },
        )
    )
    session = game(data)
    event = session.submit_action("bob", 0, "flag", {"type": "timeout"}, 0)
    assert event["outcome"]["kind"] == "draw" and event["outcome"]["winner"] is None


def test_normalized_history_counts_initial_position_and_claim_preserves_it():
    data = configuration()
    data["position_identity"] = identity()
    data["rules"].append(
        outcome_rule(
            "repeated",
            {
                "op": "all",
                "args": [
                    compare(ref("event.type"), "claim_draw"),
                    compare(ref("event.claim"), "repeated"),
                    compare(query("repetition_count", scope="position"), 3, "gte"),
                ],
            },
        )
    )
    session = game(data)
    initial_key = session.get_state()["position_history"][0]
    repeat(session, 8)
    before = session.get_state()
    assert before["position_history"].count(initial_key) == 3
    request = {"type": "claim_draw", "claim": "repeated", "intended_move": None}
    event = session.submit_action("alice", 8, "claim", request, 9)
    state = session.get_state()
    assert event["outcome"]["kind"] == "draw"
    for field in ("board", "active_side", "halfmove_count", "position_history", "quest_progress"):
        assert state[field] == before[field]
    assert state["clocks"]["remaining_ms"]["1"] == before["clocks"]["remaining_ms"]["1"] - 1
    assert GameManager.from_snapshot(state).get_state() == state


def test_intended_claim_uses_projection_without_committing_board_rights_quests_or_increment():
    data = configuration()
    data["quests"] = [
        {"id": "move-objective", "description": "A move", "when": {"op": "true"}, "reward": 5}
    ]
    data["rules"].append(
        outcome_rule(
            "projected-halfmove",
            {
                "op": "all",
                "args": [
                    compare(ref("event.type"), "claim_draw"),
                    compare(query("halfmove_count"), 1),
                ],
            },
        )
    )
    session = game(data)
    before = session.get_state()
    request = {
        "type": "claim_draw",
        "claim": "projected-halfmove",
        "intended_move": Move((0, 0), (0, 1)).to_json(),
    }
    event = session.submit_action("alice", 0, "intended", request, 1)
    after = session.get_state()
    for field in (
        "board",
        "active_side",
        "halfmove_count",
        "position_history",
        "quest_progress",
        "special_rights",
        "temporary_targets",
    ):
        assert after[field] == before[field]
    assert after["clocks"]["remaining_ms"]["1"] == 599999
    assert event["action"] == request and event["move"] is None
    assert GameManager.from_snapshot(after).get_state() == after
    changed = deepcopy(request)
    changed["intended_move"] = Move((0, 0), (0, 2)).to_json()
    with pytest.raises(TransitionError):
        session.submit_action("alice", 0, "intended", changed, 2)
    assert session.get_state() == after


@pytest.mark.parametrize(
    "actor,terminal_request",
    [
        ("mallory", {"type": "resign"}),
        ("bob", {"type": "claim_draw", "claim": "valid", "intended_move": None}),
        ("alice", {"type": "claim_draw", "claim": "unknown", "intended_move": None}),
        ("alice", {"type": "claim_draw", "claim": "permission", "intended_move": None}),
        ("alice", {"type": "resign", "winner": "alice"}),
        ("alice", {"type": "timeout", "expired_side": -1}),
    ],
)
def test_invalid_terminal_requests_cannot_use_unrelated_automatic_draw(actor, terminal_request):
    data = configuration()
    data["rules"].append(outcome_rule("automatic", {"op": "true"}))
    session = game(data)
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit_action(actor, 0, "invalid", terminal_request, 1)
    assert session.get_state() == before


def test_racing_terminal_requests_publish_one_result_and_stale_or_other_body_rejects():
    data = configuration()
    data["rules"].append(
        outcome_rule(
            "resignation", compare(ref("event.type"), "resign"), "win", ref("player.opponent.id")
        )
    )
    session = game(data)

    def submit(actor):
        try:
            return session.submit_action(actor, 0, "race-" + actor, {"type": "resign"}, 1)
        except TransitionError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, ["alice", "bob"]))
    assert sum(result is not None for result in results) == 1
    assert session.get_state()["revision"] == 1 and len(session.get_state()["events"]) == 1


def target_config(pinned=False, eligibility=True):
    data = configuration()
    data["pieces"]["role"] = {
        "symbols": {"white": "R", "black": "r"},
        "moves": [[0, 1]],
        "attacks": [[0, 1]],
        "jump": False,
        "repeat": False,
    }
    data["pieces"]["beam"] = {
        "symbols": {"white": "T", "black": "t"},
        "moves": [[1, 0]],
        "attacks": [[1, 0]],
        "jump": False,
        "repeat": True,
    }
    data["board"]["starting_pieces"] = [
        {"piece": "role", "color": "white", "squares": [[4, 2]]},
        {"piece": "token", "color": "white", "squares": [[3, 2]]},
        {"piece": "token", "color": "black", "squares": [[3, 3]]},
    ]
    if pinned:
        data["board"]["starting_pieces"].append(
            {"piece": "beam", "color": "black", "squares": [[0, 2]]}
        )
    data["initial_state"] = {
        "rule_state": {"counter": 0},
        "special_rights": {"right": True},
        "temporary_targets": {"passing": [2, 3]},
    }
    data["position_identity"] = identity(
        rights=["right"],
        rule_state=["counter"],
        targets=[{"name": "passing", "legal_capture": eligibility}],
    )
    data["rules"].append(
        {
            "id": "offer",
            "hook": "available_moves",
            "when": {
                "op": "all",
                "args": [
                    compare(ref("player.side"), 1),
                    compare(query("temporary_target", name="passing"), None, "ne"),
                ],
            },
            "effects": [
                {
                    "op": "offer_move",
                    "params": {
                        "start": [3, 2],
                        "end": query("temporary_target", name="passing"),
                        "effects": [{"op": "capture_piece", "params": {"square": [3, 3]}}],
                    },
                }
            ],
        }
    )
    data["rules"].append(
        {
            "id": "safety",
            "hook": "permits_move",
            "when": {
                "op": "not",
                "arg": {
                    "op": "test",
                    "query": "pieces_safe",
                    "params": {"kind": "role", "side": "active", "phase": "after"},
                },
            },
            "effects": [{"op": "deny", "params": {}}],
        }
    )
    return data


@pytest.mark.parametrize("pinned,expected", [(False, [2, 3]), (True, None)])
def test_temporary_target_identity_depends_on_complete_projected_capture_legality(pinned, expected):
    session = game(target_config(pinned))
    key = session.get_state()["position_history"][0]

    assert json.loads(key)["targets"]["passing"] == expected
    assert session.get_state()["revision"] == 0
    assert GameManager.from_snapshot(session.get_state()).get_state() == session.get_state()


def test_explicit_unconditional_target_keeps_pinned_target_and_selected_rights_change_identity():
    session = game(target_config(True, False))
    state = session.get_state()
    first = session._position_key(state)
    modified = deepcopy(state)
    modified["board"][0]["moved"] = not modified["board"][0]["moved"]
    assert session._position_key(modified) == first
    modified["special_rights"]["right"] = False
    assert session._position_key(modified) != first
    modified = deepcopy(state)
    modified["rule_state"]["counter"] = 1
    assert session._position_key(modified) != first


def test_identity_probe_repetition_recursion_fails_closed_before_acceptance():
    data = target_config(False)
    session = game(data)
    before = session.get_state()
    # A selected target's legality cannot itself depend on deriving its identity.
    data["rules"].append(
        {
            "id": "recursive",
            "hook": "permits_move",
            "when": compare(query("repetition_count", scope="position"), 0, "gte"),
            "effects": [{"op": "permit", "params": {}}],
        }
    )
    with pytest.raises(QueryResolutionError):
        game(data)
    assert session.get_state() == before


@pytest.mark.parametrize(
    "policy",
    [
        identity(moved_kinds=["unknown"]),
        identity(rights=["unknown"]),
        identity(targets=[{"name": "unknown", "legal_capture": True}]),
        identity(targets=[{"name": "passing", "legal_capture": 1}]),
    ],
)
def test_invalid_identity_policies_are_rejected_before_session_creation(policy):
    data = target_config(False)
    data["position_identity"] = policy
    with pytest.raises(ConfigurationError):
        validate_definition(data)
