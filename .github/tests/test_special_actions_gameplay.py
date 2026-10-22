"""Independent FR-61/69/80 special-action authorization and projection regressions."""

from copy import deepcopy
import json
from importlib import resources
from typing import Any

import pytest

from model.game.conditions import QueryResolutionError
from model.game.capture_policy import EvaluationBudgetExceeded
from model.game.definition import ConfigurationError, validate_definition
from model.game.manager import GameManager, TransitionError
from model.game.move import Move


def rule(identifier: str, hook: str, effects: list[dict], when: dict | None = None) -> dict:
    """Describe a complete real declarative rule without substitute query answers."""
    return {"id": identifier, "hook": hook, "when": when or {"op": "true"}, "effects": effects}


def config() -> dict:
    """Use renamed roles and nonstandard dimensions to expose game-name assumptions."""
    data = json.loads((resources.files("games").joinpath("chess", "config.json")).read_text())
    data.update(name="independent-specials", title="Declared authority", playable=False)
    token = deepcopy(data["pieces"]["rook"])
    token.update(
        moves=[[0, 1], [0, -1]], attacks=[[0, 1], [0, -1]], repeat=False, color_relative=False
    )
    beam = deepcopy(token)
    beam.update(
        moves=[[1, 0], [-1, 0], [0, 1], [0, -1]],
        attacks=[[1, 0], [-1, 0], [0, 1], [0, -1]],
        repeat=True,
    )
    data["pieces"] = {
        "runner": token,
        "sentinel": deepcopy(token),
        "beam": beam,
        "crowned": deepcopy(beam),
    }
    data["board"] = {
        "rows": 7,
        "columns": 9,
        "starting_pieces": [
            {"piece": "sentinel", "color": "white", "squares": [[5, 2]]},
            {"piece": "runner", "color": "white", "squares": [[5, 7]]},
            {"piece": "beam", "color": "black", "squares": [[0, 0]]},
        ],
    }
    data["rules"] = [rule("permit", "permits_move", [{"op": "permit", "params": {}}])]
    data["quests"] = []
    data["clock"] = {"initial_seconds": 30, "increment_seconds": 0}
    return data


def offer(start: list[int], end: list[int], effects: list[dict] | None = None) -> dict:
    """Offer a bounded complete intent with explicitly declared auxiliary effects."""
    return {"op": "offer_move", "params": {"start": start, "end": end, "effects": effects or []}}


def game(data: dict) -> GameManager:
    """Validate actual data and create authoritative state with fixed identities."""
    return GameManager(validate_definition(data), "special-authority", ("alice", "bob"), 0)


def unchanged_rejection(
    manager: GameManager, move: Move, error: type[Exception] = ValueError
) -> None:
    """Prove rejection preserves the complete persistable snapshot."""
    before = manager.get_state()
    with pytest.raises(error):
        manager.submit("alice", 0, "rejected", move, 1)
    assert manager.get_state() == before
    assert GameManager.from_snapshot(before).get_state() == before


def test_auxiliary_offer_effect_runs_once_and_replays_without_read_mutation() -> None:
    """FR-61/80: offered compound actions commit exactly one complete transition."""
    data = config()
    data["rules"].append(
        rule(
            "offer",
            "available_moves",
            [
                offer(
                    [5, 2],
                    [5, 4],
                    [
                        {"op": "move_piece", "params": {"start": [5, 7], "end": [5, 3]}},
                        {"op": "increment_state", "params": {"name": "applications", "amount": 1}},
                    ],
                )
            ],
        )
    )
    manager = game(data)
    before = manager.get_state()
    intent = Move((5, 2), (5, 4))
    assert intent in manager.get_valid_moves()
    assert manager.get_state() == before
    event = manager.submit("alice", 0, "compound", intent, 1)
    state = manager.get_state()
    assert state["rule_state"]["applications"] == 1
    assert {(tuple(p["square"]), p["kind"]) for p in state["board"]} == {
        ((5, 4), "sentinel"),
        ((5, 3), "runner"),
        ((0, 0), "beam"),
    }
    assert state["revision"] == len(state["events"]) == 1
    recovered = GameManager.from_snapshot(state)
    assert recovered.get_state() == state
    assert recovered.submit("alice", 0, "compound", intent, 99999) == event
    assert recovered.get_state() == state


@pytest.mark.parametrize("different_effect", [False, True])
def test_ambiguous_duplicate_wire_offers_fail_closed(different_effect: bool) -> None:
    """FR-61: duplicate intents cannot silently choose a different effect plan."""
    data = config()
    first = offer([5, 2], [5, 4])
    second = deepcopy(first)
    if different_effect:
        second["params"]["effects"] = [
            {"op": "set_state", "params": {"name": "selected", "value": True}}
        ]
    data["rules"].append(rule("duplicates", "available_moves", [first, second]))
    manager = game(data)
    unchanged_rejection(manager, Move((5, 2), (5, 4)), QueryResolutionError)
    with pytest.raises(QueryResolutionError, match="duplicate|ambiguous"):
        manager.get_valid_moves()
    assert manager.get_state()["revision"] == 0


def test_offer_never_overrides_explicit_denial_or_authorizes_unoffered_geometry() -> None:
    """FR-61: offer discovery is not permission and cannot create nearby intents."""
    data = config()
    data["rules"].append(rule("offer", "available_moves", [offer([5, 2], [5, 4])]))
    data["rules"].append(rule("deny", "permits_move", [{"op": "deny", "params": {}}]))
    unchanged_rejection(game(data), Move((5, 2), (5, 4)), TransitionError)
    data["rules"] = data["rules"][:-1]
    unchanged_rejection(game(data), Move((5, 2), (5, 5)), TransitionError)


def test_offer_cannot_claim_an_opponent_source() -> None:
    """FR-80: authored move discovery cannot impersonate the other participant."""
    data = config()
    data["rules"].append(rule("wrong-owner", "available_moves", [offer([0, 0], [0, 2])]))
    manager = game(data)
    unchanged_rejection(manager, Move((5, 2), (5, 4)), QueryResolutionError)


def safe_condition() -> dict:
    """Require the renamed active safety role on the complete prospective board."""
    return {
        "op": "test",
        "query": "pieces_safe",
        "params": {"kind": "sentinel", "side": "active", "phase": "after"},
    }


def test_prospective_pin_rejects_exposure_and_auxiliary_capture_can_remove_the_threat() -> None:
    """FR-61: projected role safety uses complete geometry, not piece-name guesses."""
    data = config()
    data["board"]["starting_pieces"] = [
        {"piece": "sentinel", "color": "white", "squares": [[6, 4]]},
        {"piece": "runner", "color": "white", "squares": [[4, 4]]},
        {"piece": "beam", "color": "black", "squares": [[0, 4]]},
    ]
    data["rules"][0]["when"] = safe_condition()
    manager = game(data)
    unchanged_rejection(manager, Move((4, 4), (4, 5)), TransitionError)
    data["rules"].append(
        rule(
            "remove-threat",
            "available_moves",
            [
                offer(
                    [4, 4],
                    [4, 6],
                    [
                        {"op": "capture_piece", "params": {"square": [0, 4]}},
                    ],
                )
            ],
        )
    )
    manager = game(data)
    event = manager.submit("alice", 0, "safe-special", Move((4, 4), (4, 6)), 1)
    state = manager.get_state()
    assert event["captured"] == [[0, 4]]
    assert {tuple(p["square"]) for p in state["board"]} == {(6, 4), (4, 6)}
    assert GameManager.from_snapshot(state).get_state() == state


def test_auxiliary_capture_exposing_the_destination_rolls_back_every_effect() -> None:
    """FR-61/80: safety must include an offer's removal effects before permission."""
    data = config()
    data["board"]["starting_pieces"] = [
        {"piece": "sentinel", "color": "white", "squares": [[6, 4]]},
        {"piece": "runner", "color": "black", "squares": [[3, 5]]},
        {"piece": "beam", "color": "black", "squares": [[0, 5]]},
    ]
    data["rules"][0]["when"] = safe_condition()
    data["rules"].append(
        rule(
            "exposure",
            "available_moves",
            [
                offer(
                    [6, 4],
                    [6, 5],
                    [
                        {"op": "set_state", "params": {"name": "before-denial", "value": True}},
                        {"op": "capture_piece", "params": {"square": [3, 5]}},
                    ],
                )
            ],
        )
    )
    unchanged_rejection(game(data), Move((6, 4), (6, 5)), TransitionError)


def test_capture_promotion_requires_choice_and_replays_replacement() -> None:
    """FR-61: capture and explicit promotion are one atomic replayable action."""
    data = config()
    data["pieces"]["runner"].update(
        moves=[[-1, 0]],
        attacks=[[-1, 1]],
        promotion={
            "rank": "far",
            "mode": "choice",
            "options": ["crowned", "sentinel"],
            "stop_capture": False,
        },
    )
    data["board"]["starting_pieces"] = [
        {"piece": "runner", "color": "white", "squares": [[1, 2]]},
        {"piece": "beam", "color": "black", "squares": [[0, 3]]},
    ]
    manager = game(data)
    unchanged_rejection(manager, Move((1, 2), (0, 3)), TransitionError)
    unchanged_rejection(manager, Move((1, 2), (0, 3), promotion="beam"), TransitionError)
    accepted = Move((1, 2), (0, 3), promotion="crowned")
    assert accepted in manager.get_valid_moves()
    event = manager.submit("alice", 0, "promotion", accepted, 1)
    state = manager.get_state()
    assert state["board"] == [{"square": [0, 3], "kind": "crowned", "side": 1, "moved": True}]
    assert event["captured"] == [[0, 3]]
    assert GameManager.from_snapshot(state).get_state() == state


def test_automatic_crowning_stops_capture_chain_on_the_configured_boundary() -> None:
    """FR-61: a declared stop rank accepts the prefix and rejects continuation."""
    data = config()
    data["pieces"]["runner"].update(
        moves=[[-1, 1], [-1, -1]],
        attacks=[[-1, 1], [-1, -1], [1, 1], [1, -1]],
        capture_policy={
            "flying": False,
            "land_anywhere": False,
            "deferred_removal": False,
            "max_nodes": 1000,
        },
        promotion={
            "rank": "far",
            "mode": "automatic",
            "options": ["crowned"],
            "stop_capture": True,
        },
    )
    data["board"]["starting_pieces"] = [
        {"piece": "runner", "color": "white", "squares": [[2, 1]]},
        {"piece": "beam", "color": "black", "squares": [[1, 2], [1, 4]]},
    ]
    manager = game(data)
    unchanged_rejection(manager, Move((2, 1), (2, 5), hops=((0, 3), (2, 5))), TransitionError)
    unchanged_rejection(manager, Move((2, 1), (0, 3), promotion="crowned"), TransitionError)
    event = manager.submit("alice", 0, "crown", Move((2, 1), (0, 3)), 1)
    state = manager.get_state()
    assert event["captured"] == [[1, 2]]
    assert {(tuple(p["square"]), p["kind"]) for p in state["board"]} == {
        ((0, 3), "crowned"),
        ((1, 4), "beam"),
    }
    assert GameManager.from_snapshot(state).get_state() == state


@pytest.mark.parametrize(
    "query,params",
    [
        ("integer", {"operation": "add", "left": 2**63 - 1, "right": 1}),
        ("integer", {"operation": "floor_divide", "left": 1, "right": 0}),
        ("integer", {"operation": "add", "left": True, "right": 1}),
        ("square_offset", {"square": [5, 2], "offset": [False, 1]}),
    ],
)
def test_nested_effect_queries_fail_closed_for_overflow_and_invalid_types(
    query: str, params: dict
) -> None:
    """FR-69/80: auxiliary nested expressions remain bounded typed operations."""
    data = config()
    data["rules"].append(
        rule(
            "bad-expression",
            "available_moves",
            [
                offer(
                    [5, 2],
                    [5, 4],
                    [
                        {
                            "op": "set_state",
                            "params": {
                                "name": "invalid",
                                "value": {"query": query, "params": params},
                            },
                        },
                    ],
                )
            ],
        )
    )
    unchanged_rejection(game(data), Move((5, 2), (5, 4)), QueryResolutionError)


@pytest.mark.parametrize(
    "node",
    [
        {"ref": "move.__class__"},
        {"ref": "move.start", "payload": 1},
        {"query": "__import__", "params": {}},
    ],
)
def test_hostile_nested_reference_nodes_never_enter_an_offer(node: Any) -> None:
    """FR-80: closed nested expressions cannot escape the declarative vocabulary."""
    data = config()
    data["rules"].append(
        rule(
            "hostile",
            "available_moves",
            [
                offer(
                    [5, 2],
                    [5, 4],
                    [
                        {"op": "set_state", "params": {"name": "hostile", "value": node}},
                    ],
                )
            ],
        )
    )
    with pytest.raises(ConfigurationError):
        validate_definition(data)


def test_available_move_discovery_cannot_recurse_into_uncomputed_legal_counts() -> None:
    """FR-69: discovery rejects recursive state demands rather than recursing."""
    data = config()
    condition = {
        "op": "compare",
        "relation": "gt",
        "left": {
            "query": "legal_move_count",
            "params": {"side": "active"},
        },
        "right": 0,
    }
    data["rules"].append(rule("recursive", "available_moves", [offer([5, 2], [5, 4])], condition))
    manager = game(data)
    unchanged_rejection(manager, Move((5, 2), (5, 4)), QueryResolutionError)
    with pytest.raises(QueryResolutionError):
        manager.get_valid_moves()


def test_aggregate_budget_covers_query_work_inside_special_offer_discovery() -> None:
    """FR-69/80: valid bounded rule syntax cannot amplify unbounded discovery."""
    data = config()
    data["board"]["rows"] = 64
    data["board"]["columns"] = 64
    repeated_query = {
        "op": "compare",
        "relation": "ne",
        "left": {"query": "pieces_matching", "params": {}},
        "right": [],
    }
    condition = {"op": "all", "args": [deepcopy(repeated_query) for _ in range(8)]}
    data["rules"].extend(
        rule(f"work-{index}", "available_moves", [offer([5, 2], [5, 4])], condition)
        for index in range(127)
    )
    manager = game(data)
    before = manager.get_state()
    for _ in range(2):
        with pytest.raises(EvaluationBudgetExceeded):
            manager.get_valid_moves()
        assert manager.get_state() == before
    with pytest.raises(EvaluationBudgetExceeded):
        manager.submit("alice", 0, "overload", Move((5, 2), (5, 4)), 1)
    assert manager.get_state() == before


def test_black_capture_promotes_on_its_configured_far_side_of_a_nonstandard_board() -> None:
    """FR-61: promotion uses side-relative configured ranks and renamed kinds."""
    data = config()
    data["pieces"]["runner"].update(
        moves=[[1, 0]],
        attacks=[[1, 1]],
        promotion={
            "rank": "far",
            "mode": "choice",
            "options": ["crowned"],
            "stop_capture": False,
        },
    )
    data["board"]["starting_pieces"] = [
        {"piece": "sentinel", "color": "white", "squares": [[2, 0], [6, 3]]},
        {"piece": "runner", "color": "black", "squares": [[5, 2]]},
    ]
    manager = game(data)
    manager.submit("alice", 0, "first", Move((2, 0), (2, 1)), 1)
    before = manager.get_state()
    with pytest.raises(TransitionError):
        manager.submit("bob", 1, "missing-choice", Move((5, 2), (6, 3)), 2)
    assert manager.get_state() == before
    event = manager.submit(
        "bob", 1, "black-promotion", Move((5, 2), (6, 3), promotion="crowned"), 2
    )
    state = manager.get_state()
    assert {tuple(p["square"]): (p["kind"], p["side"]) for p in state["board"]} == {
        (2, 1): ("sentinel", 1),
        (6, 3): ("crowned", -1),
    }
    assert event["captured"] == [[6, 3]]
    assert GameManager.from_snapshot(state).get_state() == state


def test_auxiliary_temporary_target_must_fit_the_configured_board() -> None:
    """FR-61/80: transition effects preserve the target-coordinate state contract."""
    data = config()
    data["initial_state"] = {
        "rule_state": {},
        "special_rights": {},
        "temporary_targets": {"passing": None},
    }
    # This custom definition deliberately does not declare the chess-specific
    # castling/en-passant state selected by the bundled repetition policy.
    data.pop("position_identity", None)
    data["rules"].append(
        rule(
            "outside-target",
            "available_moves",
            [
                offer(
                    [5, 2],
                    [5, 4],
                    [
                        {"op": "set_target", "params": {"name": "passing", "value": [7, 0]}},
                    ],
                )
            ],
        )
    )
    unchanged_rejection(game(data), Move((5, 2), (5, 4)), TransitionError)
