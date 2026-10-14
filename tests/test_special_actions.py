"""FR-13/14/15/16/69: game-neutral offers, projected safety and promotion behavior."""

import json

import pytest

from engine.model.game.conditions import QueryResolutionError
from engine.model.game.configuration import ConfigurationError, validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move


def spec(*, repeat=False, diagonal=False):
    directions = (
        [[-1, -1], [-1, 1], [1, -1], [1, 1]] if diagonal else [[-1, 0], [1, 0], [0, -1], [0, 1]]
    )
    return {
        "symbols": {"white": "W", "black": "B"},
        "moves": directions,
        "attacks": directions,
        "jump": False,
        "repeat": repeat,
    }


def config(placements, rows=8, columns=8):
    return {
        "schema_version": 2,
        "name": "neutral",
        "title": "Neutral",
        "default": False,
        "playable": False,
        "board": {"rows": rows, "columns": columns, "starting_pieces": placements},
        "pieces": {
            "sentinel": spec(),
            "carrier": spec(repeat=True),
            "runner": spec(diagonal=True),
            "crowned": spec(diagonal=True),
        },
        "clock": {"initial_seconds": 600, "increment_seconds": 1},
        "exports": [],
        "appearance": {},
        "rules": [rule("permission", "permits_move", {"op": "true"}, "permit", {})],
        "quests": [],
    }


def place(kind, side, *squares):
    return {"piece": kind, "color": side, "squares": [list(square) for square in squares]}


def rule(identity, hook, when, op, params):
    return {"id": identity, "hook": hook, "when": when, "effects": [{"op": op, "params": params}]}


def white():
    return {"op": "compare", "relation": "eq", "left": {"ref": "player.side"}, "right": 1}


def query(query_name, **params):
    return {"query": query_name, "params": params}


def game(data):
    return GameManager(validate_definition(data), "special", ("alice", "bob"), 0)


def record(snapshot, square):
    return next((piece for piece in snapshot["board"] if piece["square"] == list(square)), None)


@pytest.mark.parametrize("rows,columns,rank,file", [(8, 8, 7, 1), (7, 9, 5, 2)])
def test_relocated_offers_derive_auxiliary_coordinates_from_declared_data(
    rows, columns, rank, file
):
    data = config(
        [
            place("sentinel", "white", (rank, file)),
            place("carrier", "white", (rank, columns - 1)),
            place("sentinel", "black", (0, 0)),
        ],
        rows,
        columns,
    )
    source = query(
        "json_value",
        value=query("pieces_matching", kind="sentinel", side="active"),
        path=[0, "square"],
    )
    end = query("square_offset", square=source, offset=[0, 2])
    last_file = query(
        "integer", operation="subtract", left=query("board_dimension", axis="columns"), right=1
    )
    data["rules"].append(
        rule(
            "offer",
            "available_moves",
            white(),
            "offer_move",
            {
                "start": source,
                "end": end,
                "effects": [
                    {
                        "op": "move_piece",
                        "params": {
                            "start": [rank, last_file],
                            "end": query("square_offset", square=source, offset=[0, 1]),
                        },
                    },
                    {"op": "increment_state", "params": {"name": "auxiliary", "amount": 1}},
                ],
            },
        )
    )
    session = game(data)
    intent = Move((rank, file), (rank, file + 2))
    assert intent in session.get_valid_moves()
    event = session.submit("alice", 0, "castle-like", intent, 10)
    state = session.get_state()
    assert record(state, (rank, file + 2))["kind"] == "sentinel"
    assert record(state, (rank, file + 1))["kind"] == "carrier"
    assert record(state, (rank, columns - 1)) is None
    assert state["rule_state"]["auxiliary"] == 1
    assert session.submit("alice", 0, "castle-like", intent, 20) == event
    assert GameManager.from_snapshot(state).get_state() == state


def test_projected_role_safety_rejects_pinned_geometry_without_mutation():
    data = config(
        [
            place("sentinel", "white", (7, 4)),
            place("carrier", "white", (6, 4)),
            place("carrier", "black", (0, 4)),
            place("sentinel", "black", (0, 0)),
        ]
    )
    data["rules"].append(
        rule(
            "safety",
            "permits_move",
            {
                "op": "not",
                "arg": {
                    "op": "test",
                    "query": "pieces_safe",
                    "params": {"kind": "sentinel", "side": "active", "phase": "after"},
                },
            },
            "deny",
            {},
        )
    )
    session = game(data)
    before = session.get_state()
    pinned = Move((6, 4), (6, 5))
    assert pinned not in session.get_valid_moves()
    with pytest.raises(TransitionError):
        session.submit("alice", 0, "pinned", pinned, 1)
    assert session.get_state() == before
    accepted = Move((6, 4), (0, 4))
    assert accepted in session.get_valid_moves()
    session.submit("alice", 0, "remove-threat", accepted, 1)
    assert record(session.get_state(), (0, 4))["side"] == 1


def test_safety_sees_auxiliary_postmove_effects_and_cannot_apply_them_twice():
    data = config(
        [
            place("sentinel", "white", (7, 4)),
            place("runner", "white", (4, 0)),
            place("carrier", "white", (6, 4)),
            place("carrier", "black", (0, 4)),
            place("sentinel", "black", (0, 0)),
        ]
    )
    data["rules"].append(
        rule(
            "auxiliary",
            "on_move_made",
            {"op": "true"},
            "move_piece",
            {"start": [6, 4], "end": [6, 5]},
        )
    )
    data["rules"].append(
        rule(
            "safety",
            "permits_move",
            {
                "op": "not",
                "arg": {
                    "op": "test",
                    "query": "pieces_safe",
                    "params": {"kind": "sentinel", "side": "active", "phase": "after"},
                },
            },
            "deny",
            {},
        )
    )
    session = game(data)
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit("alice", 0, "exposes-role", Move((4, 0), (3, 1)), 1)
    assert session.get_state() == before


def test_off_square_capture_uses_pinned_target_and_clears_it_with_atomic_history():
    data = config(
        [
            place("runner", "white", (3, 2)),
            place("runner", "black", (3, 3)),
            place("sentinel", "black", (0, 0)),
        ]
    )
    data["initial_state"] = {
        "rule_state": {},
        "special_rights": {"passing": True},
        "temporary_targets": {"passing": [2, 3]},
    }
    data["rules"].append(
        rule(
            "pass",
            "available_moves",
            white(),
            "offer_move",
            {
                "start": [3, 2],
                "end": query("temporary_target", name="passing"),
                "effects": [
                    {
                        "op": "capture_piece",
                        "params": {
                            "square": query(
                                "square_offset",
                                square=query("temporary_target", name="passing"),
                                offset=[1, 0],
                            )
                        },
                    },
                    {"op": "set_rights", "params": {"name": "passing", "value": False}},
                ],
            },
        )
    )
    session = game(data)
    event = session.submit("alice", 0, "passing", Move((3, 2), (2, 3)), 1)
    state = session.get_state()
    assert record(state, (3, 3)) is None and record(state, (2, 3))["side"] == 1
    assert event["captured"] == [[3, 3]] and state["halfmove_count"] == 0
    assert state["temporary_targets"]["passing"] is None
    assert state["special_rights"]["passing"] is False
    assert GameManager.from_snapshot(state).get_state() == state


@pytest.mark.parametrize("deny_first", [True, False])
def test_deny_wins_over_offer_and_permission_order_with_rollback(deny_first):
    data = config([place("sentinel", "white", (7, 1)), place("sentinel", "black", (0, 0))])
    deny = rule("deny", "permits_move", {"op": "true"}, "deny", {})
    data["rules"].insert(0 if deny_first else len(data["rules"]), deny)
    data["rules"].append(
        rule(
            "offer",
            "available_moves",
            white(),
            "offer_move",
            {
                "start": [7, 1],
                "end": [7, 3],
                "effects": [{"op": "increment_state", "params": {"name": "counter", "amount": 1}}],
            },
        )
    )
    session = game(data)
    before = session.get_state()
    assert session.get_valid_moves() == []
    with pytest.raises(TransitionError):
        session.submit("alice", 0, "denied", Move((7, 1), (7, 3)), 1)
    assert session.get_state() == before


def test_duplicate_offers_are_ambiguous_without_geometric_fallback():
    data = config([place("sentinel", "white", (7, 1)), place("sentinel", "black", (0, 0))])
    for identity in ("one", "two"):
        data["rules"].append(
            rule(
                identity, "available_moves", white(), "offer_move", {"start": [7, 1], "end": [7, 2]}
            )
        )
    session = game(data)
    before = session.get_state()
    with pytest.raises(QueryResolutionError, match="ambiguous"):
        session.get_valid_moves()
    with pytest.raises(QueryResolutionError, match="ambiguous"):
        session.submit("alice", 0, "bad", Move((7, 1), (7, 2)), 1)
    assert session.get_state() == before


@pytest.mark.parametrize("choice", [None, "carrier", "not-configured"])
def test_required_promotion_rejects_missing_and_unoffered_choices(choice):
    data = config([place("runner", "white", (1, 2)), place("sentinel", "black", (7, 7))])
    data["pieces"]["runner"]["promotion"] = {
        "rank": "far",
        "options": ["crowned", "sentinel"],
        "mode": "choice",
        "stop_capture": False,
    }
    session = game(data)
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit("alice", 0, "bad-choice", Move((1, 2), (0, 3), promotion=choice), 1)
    assert session.get_state() == before


def test_promotion_choices_are_real_intents_and_replay_the_selected_kind():
    data = config(
        [place("runner", "white", (1, 2)), place("sentinel", "black", (7, 7))], rows=10, columns=10
    )
    data["pieces"]["runner"]["promotion"] = {
        "rank": "far",
        "options": ["crowned", "sentinel"],
        "mode": "choice",
        "stop_capture": False,
    }
    session = game(data)
    options = [move for move in session.get_valid_moves() if move.end_pos == (0, 3)]
    assert {move.promotion for move in options} == {"crowned", "sentinel"}
    session.submit("alice", 0, "choice", Move((1, 2), (0, 3), promotion="sentinel"), 1)
    state = session.get_state()
    assert record(state, (0, 3))["kind"] == "sentinel"
    assert GameManager.from_snapshot(state).get_state() == state


@pytest.mark.parametrize(
    "stop,expected_hops,expected_kind",
    [(True, ((0, 3),), "crowned"), (False, ((0, 3), (2, 5)), "runner")],
)
def test_capture_crowning_boundary_is_configured_not_inferred(stop, expected_hops, expected_kind):
    data = config(
        [place("runner", "white", (2, 1)), place("runner", "black", (1, 2), (1, 4))],
        rows=6,
        columns=8,
    )
    data["pieces"]["runner"]["capture_policy"] = {
        "flying": False,
        "land_anywhere": False,
        "deferred_removal": True,
        "max_nodes": 100,
    }
    data["pieces"]["runner"]["promotion"] = {
        "rank": "far",
        "options": ["crowned"],
        "mode": "automatic",
        "stop_capture": stop,
    }
    session = game(data)
    expected = Move((2, 1), expected_hops[-1], expected_hops)
    assert expected in session.get_valid_moves()
    forbidden = Move((2, 1), (2, 5), ((0, 3), (2, 5))) if stop else Move((2, 1), (0, 3))
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit("alice", 0, "incomplete", forbidden, 1)
    assert session.get_state() == before
    event = session.submit("alice", 0, "chain", expected, 1)
    assert len(event["captured"]) == (1 if stop else 2)
    assert record(session.get_state(), expected.end_pos)["kind"] == expected_kind


@pytest.mark.parametrize(
    "expr",
    [
        query("integer", operation="floor_divide", left=1, right=0),
        query("integer", operation="add", left=True, right=1),
        query("integer", operation="add", left=2**63 - 1, right=1),
        query("json_value", value={}, path=["absent", True]),
        query("square_offset", square=[7, 1], offset=[True, 1]),
    ],
)
def test_malicious_nested_query_cannot_authorize_offers(expr):
    data = config([place("sentinel", "white", (7, 1)), place("sentinel", "black", (0, 0))])
    data["rules"].append(
        rule(
            "unsafe", "available_moves", white(), "offer_move", {"start": [7, 1], "end": [expr, 3]}
        )
    )
    session = game(data)
    before = session.get_state()
    with pytest.raises((QueryResolutionError, ValueError)):
        session.submit("alice", 0, "bad", Move((7, 1), (7, 3)), 1)
    assert session.get_state() == before


def test_missing_json_path_null_cannot_implicitly_permit_an_action():
    data = config([place("sentinel", "white", (7, 1)), place("sentinel", "black", (0, 0))])
    data["rules"] = [
        rule(
            "missing",
            "permits_move",
            {
                "op": "compare",
                "relation": "eq",
                "left": query("json_value", value=query("last_action"), path=["move", "start"]),
                "right": [7, 1],
            },
            "permit",
            {},
        )
    ]
    session = game(data)
    before = session.get_state()
    with pytest.raises(TransitionError):
        session.submit("alice", 0, "missing", Move((7, 1), (7, 2)), 1)
    assert session.get_state() == before


@pytest.mark.parametrize("explicit", [False, True])
def test_snapshot_keeps_original_optional_field_presence_and_replays_exactly(explicit):
    data = config([place("sentinel", "white", (7, 1)), place("sentinel", "black", (0, 0))])
    if explicit:
        data["initial_state"] = {"rule_state": {}, "special_rights": {}, "temporary_targets": {}}
        data["halfmove_reset"] = None
    session = game(data)
    session.submit("alice", 0, "saved", Move((7, 1), (7, 2)), 1)
    snapshot = session.get_state()
    assert ("initial_state" in snapshot["config"]) is explicit
    assert ("halfmove_reset" in snapshot["config"]) is explicit
    assert GameManager.from_snapshot(snapshot).get_state() == snapshot


def test_changed_pinned_halfmove_policy_cannot_replay_a_different_observed_state():
    data = config([place("sentinel", "white", (7, 1)), place("sentinel", "black", (0, 0))])
    session = game(data)
    session.submit("alice", 0, "saved", Move((7, 1), (7, 2)), 1)
    snapshot = session.get_state()
    assert snapshot["halfmove_count"] == 1
    snapshot["config"]["halfmove_reset"] = {"op": "true"}
    with pytest.raises(TransitionError, match="replay"):
        GameManager.from_snapshot(snapshot)


def test_configured_extra_halfmove_reset_and_new_target_survive_reconstruction():
    data = config([place("sentinel", "white", (7, 1)), place("sentinel", "black", (0, 0))])
    data["initial_state"] = {
        "rule_state": {"seed": 3},
        "special_rights": {"right": True},
        "temporary_targets": {"old": [6, 1]},
    }
    data["halfmove_reset"] = {"op": "true"}
    data["rules"].append(
        rule(
            "target",
            "on_move_made",
            {"op": "true"},
            "set_target",
            {"name": "new", "value": {"ref": "move.end"}},
        )
    )
    session = game(data)
    session.submit("alice", 0, "lifecycle", Move((7, 1), (7, 2)), 1)
    snapshot = session.get_state()
    assert snapshot["halfmove_count"] == 0
    assert snapshot["rule_state"]["seed"] == 3
    assert snapshot["temporary_targets"] == {"old": None, "new": [7, 2]}
    assert GameManager.from_snapshot(snapshot).get_state() == snapshot


@pytest.mark.parametrize(
    "policy",
    [
        {"rank": "far", "options": ["not-configured"], "mode": "choice", "stop_capture": False},
        {
            "rank": "far",
            "options": ["crowned", "sentinel"],
            "mode": "automatic",
            "stop_capture": True,
        },
        {"rank": "far", "options": ["crowned"], "mode": "automatic", "stop_capture": 1},
    ],
)
def test_malformed_promotion_policy_fails_before_session_creation(policy):
    data = config([place("runner", "white", (1, 2)), place("sentinel", "black", (7, 7))])
    data["pieces"]["runner"]["promotion"] = policy
    with pytest.raises(ConfigurationError):
        validate_definition(data)


def test_black_far_rank_and_automatic_crowning_use_configured_rows():
    data = config(
        [place("sentinel", "white", (0, 0)), place("runner", "black", (4, 2))], rows=6, columns=7
    )
    data["pieces"]["runner"]["promotion"] = {
        "rank": "far",
        "options": ["crowned"],
        "mode": "automatic",
        "stop_capture": False,
    }
    session = game(data)
    session.submit("alice", 0, "first", Move((0, 0), (0, 1)), 1)
    intent = Move((4, 2), (5, 3))
    assert intent in session.get_valid_moves()
    session.submit("bob", 1, "crowning", intent, 2)
    assert record(session.get_state(), (5, 3))["kind"] == "crowned"


def test_available_hook_cannot_request_recursive_legal_counts():
    data = config([place("sentinel", "white", (7, 1)), place("sentinel", "black", (0, 0))])
    data["rules"].append(
        rule(
            "recursive",
            "available_moves",
            {
                "op": "compare",
                "relation": "gt",
                "left": query("legal_move_count", side="active"),
                "right": 0,
            },
            "offer_move",
            {"start": [7, 1], "end": [7, 3]},
        )
    )
    session = game(data)
    before = session.get_state()
    with pytest.raises(QueryResolutionError):
        session.get_valid_moves()
    assert session.get_state() == before
