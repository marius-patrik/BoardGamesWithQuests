"""Behavioral regressions for typed immutable JSON rule query boundaries."""

from copy import deepcopy

import pytest

from engine.model.game.conditions import ConditionEvaluator, QueryResolutionError
from engine.model.game.snapshot_queries import SnapshotQueries


def compare(relation: str, left: object, right: object) -> bool:
    evaluator = ConditionEvaluator({}, {"game.left": left, "game.right": right})
    return evaluator.evaluate(
        {
            "op": "compare",
            "relation": relation,
            "left": {"ref": "game.left"},
            "right": {"ref": "game.right"},
        }
    )


@pytest.mark.parametrize(
    "left,right",
    [
        (True, 1),
        (False, 0),
        (1, 1.0),
        ([True], [1]),
        ({"a": [False]}, {"a": [0]}),
        ([{"a": [1]}], [{"a": [1.0]}]),
    ],
)
def test_recursive_comparison_cannot_authorize_coerced_values(left: object, right: object) -> None:
    assert compare("eq", left, right) is False
    assert compare("ne", left, right) is True
    assert compare("in", left, [right]) is False


@pytest.mark.parametrize("value", [None, True, 1, 1.0, "x", [1, {"x": False}], {"x": [True]}])
def test_equal_typed_values_match_including_nested_membership(value: object) -> None:
    assert compare("eq", value, deepcopy(value)) is True
    assert compare("ne", value, deepcopy(value)) is False
    assert compare("in", value, [deepcopy(value)]) is True


def test_string_membership_and_object_key_membership_remain_supported() -> None:
    assert compare("in", "a", "cat") is True
    assert compare("in", "a", {"a": 1}) is True
    assert compare("in", "z", {"a": 1}) is False
    with pytest.raises(QueryResolutionError):
        compare("in", True, {"a": 1})


def route(count: int = 1) -> dict:
    return {
        "start": [0, 0],
        "steps": [{"captured": [2 * i + 1, 1], "landing": [2 * i + 2, 0]} for i in range(count)],
    }


def snapshot() -> dict:
    return {
        "capture_paths": {"active": [route()], "opponent": [route(3)]},
        "move_attributes": {"captures": 1, "path": [[0, 0], [2, 0]]},
        "rule_state": {"counter": {"value": [1]}},
        "special_rights": {"right": {"allowed": True}},
        "temporary_targets": {"target": [1, 1]},
        "promotion_options": {"active": ["promoted"], "opponent": []},
        "position_key": "key",
        "position_history": ["key", "other", "key"],
        "clocks": {"active": 100, "opponent": 0},
        "events": [{"action": "move"}],
        "halfmove_count": 0,
        "last_action": {"path": [[0, 0], [2, 0]]},
        "legal_move_counts": {"active": 2, "opponent": 0},
        "participants": {
            "active": {"id": "first", "side": 1},
            "opponent": {"id": "second", "side": -1},
        },
        "position": {"board": [["piece"]], "active": 1},
        "quest_progress": {
            "active": {"capture": {"active": 1, "target": 2, "completed": False}},
            "opponent": {"capture": {"active": 2, "target": 2, "completed": True}},
        },
    }


def test_side_scoped_capture_queries_do_not_borrow_opponents_routes() -> None:
    data = snapshot()
    queries = SnapshotQueries(data)
    assert queries.capture_count({"scope": "maximum"}) == 1
    assert queries.capture_paths({"side": "opponent"}) is True
    data["capture_paths"]["active"] = []
    queries = SnapshotQueries(data)
    assert queries.capture_paths({"side": "active"}) is False
    assert queries.capture_paths({"side": "opponent"}) is True
    assert queries.capture_count({"scope": "maximum"}) == 0


@pytest.mark.parametrize(
    "routes",
    [
        [],
        {"active": []},
        {"active": [], "opponent": [], "other": []},
        {"active": [{"steps": []}], "opponent": []},
        {"active": [{"start": [0, 0], "steps": []}], "opponent": []},
        {"active": [{"start": [True, 0], "steps": route()["steps"]}], "opponent": []},
        {"active": [{"start": [0, -1], "steps": route()["steps"]}], "opponent": []},
        {"active": [{"start": [0, 0], "steps": [{"landing": [2, 0]}]}], "opponent": []},
        {"active": [{"start": [0, 0], "steps": route()["steps"] * 2}], "opponent": []},
        {"active": [], "opponent": ["malformed"]},
        {"active": [route()] * 129, "opponent": []},
    ],
)
def test_malformed_routes_fail_closed_without_changing_input(routes: object) -> None:
    data = {"capture_paths": routes}
    unchanged = deepcopy(data)
    queries = SnapshotQueries(data)
    with pytest.raises(QueryResolutionError):
        queries.capture_paths({"side": "active"})
    with pytest.raises(QueryResolutionError):
        queries.capture_count({"scope": "maximum"})
    assert data == unchanged


@pytest.mark.parametrize(
    "name,params,path",
    [
        ("rule_state", {"name": "counter"}, ["value"]),
        ("special_rights", {"name": "right"}, []),
        ("temporary_target", {"name": "target"}, []),
        ("move_attribute", {"name": "path"}, []),
        ("promotion_options", {"side": "active"}, []),
        ("last_action", {}, ["path"]),
        ("participant", {"side": "active"}, []),
        ("position", {}, ["board"]),
        ("quest_progress", {"side": "active", "name": "capture"}, []),
    ],
)
def test_query_inputs_and_results_cannot_mutate_bound_snapshot(
    name: str, params: dict, path: list
) -> None:
    data = snapshot()
    queries = SnapshotQueries(data)
    operation = queries.bindings()[name]
    expected = operation(params)
    data.clear()
    result = operation(params)
    target = result
    for key in path:
        target = target[key]
    target.clear()
    assert operation(params) == expected


def test_six_pure_queries_report_authoritative_metadata() -> None:
    queries = SnapshotQueries(snapshot())
    assert queries.halfmove_count({}) == 0
    assert queries.last_action({}) == {"path": [[0, 0], [2, 0]]}
    assert queries.legal_move_count({"side": "active"}) == 2
    assert queries.legal_move_count({"side": "opponent"}) == 0
    assert queries.participant({"side": "opponent"}) == {"id": "second", "side": -1}
    assert queries.position({}) == {"board": [["piece"]], "active": 1}
    assert queries.quest_progress({"side": "opponent", "name": "capture"}) == {
        "active": 2,
        "target": 2,
        "completed": True,
    }
    assert SnapshotQueries({"last_action": None}).last_action({}) is None
    assert queries.repetition_count({"scope": "position"}) == 2
    assert queries.history_count({}) == 1
    assert queries.clock_remaining({"side": "opponent"}) == 0


@pytest.mark.parametrize(
    "name,params,field,value",
    [
        ("halfmove_count", {}, "halfmove_count", True),
        ("halfmove_count", {}, "halfmove_count", -1),
        ("last_action", {}, "last_action", []),
        ("legal_move_count", {"side": "active"}, "legal_move_counts", {"active": False}),
        ("participant", {"side": "active"}, "participants", {"active": {"id": "", "side": 1}}),
        ("participant", {"side": "active"}, "participants", {"active": {"id": "x", "side": True}}),
        ("position", {}, "position", []),
        (
            "quest_progress",
            {"side": "active", "name": "capture"},
            "quest_progress",
            {"active": {"capture": {"active": 0, "target": 0, "completed": False}}},
        ),
        (
            "quest_progress",
            {"side": "active", "name": "capture"},
            "quest_progress",
            {"active": {"capture": {"active": True, "target": 1, "completed": False}}},
        ),
    ],
)
def test_malformed_authoritative_fields_are_not_guessed(
    name: str, params: dict, field: str, value: object
) -> None:
    data = snapshot()
    data[field] = value
    with pytest.raises(QueryResolutionError):
        SnapshotQueries(data).bindings()[name](params)
    del data[field]
    with pytest.raises(QueryResolutionError):
        SnapshotQueries(data).bindings()[name](params)


@pytest.mark.parametrize(
    "name,params",
    [
        ("halfmove_count", {"extra": 1}),
        ("last_action", {"index": 0}),
        ("legal_move_count", {"side": 1}),
        ("participant", {"side": True}),
        ("position", {"name": "board"}),
        ("quest_progress", {"side": "active"}),
        ("quest_progress", {"side": "active", "name": "unknown"}),
        ("capture_paths", {"side": "unknown"}),
        ("capture_count", {"scope": "unknown"}),
    ],
)
def test_unknown_query_parameters_fail_closed(name: str, params: dict) -> None:
    data = snapshot()
    unchanged = deepcopy(data)
    with pytest.raises(QueryResolutionError):
        SnapshotQueries(data).bindings()[name](params)
    assert data == unchanged


@pytest.mark.parametrize(
    "value", [{"x": float("nan")}, {1: "coerced"}, {"x": (1, 2)}, {"x": object()}]
)
def test_non_json_snapshots_are_rejected(value: dict) -> None:
    with pytest.raises(QueryResolutionError):
        SnapshotQueries(value)


def test_capture_enumeration_accepts_boundary_and_rejects_overlong_chain() -> None:
    data = {"capture_paths": {"active": [route(128)], "opponent": []}}
    assert SnapshotQueries(data).capture_count({"scope": "maximum"}) == 128
    data["capture_paths"]["active"] = [route(129)]
    with pytest.raises(QueryResolutionError):
        SnapshotQueries(data).capture_count({"scope": "maximum"})


def test_oversized_or_overdeep_snapshots_do_not_bind_queries() -> None:
    with pytest.raises(QueryResolutionError, match="1 MiB"):
        SnapshotQueries({"value": "x" * 1048576})
    nested = {}
    for _ in range(65):
        nested = {"value": nested}
    with pytest.raises(QueryResolutionError):
        SnapshotQueries(nested)
