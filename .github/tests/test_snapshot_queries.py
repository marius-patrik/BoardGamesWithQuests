"""Public data-only behavior of read-only authoritative snapshot queries."""

from __future__ import annotations

import pytest

from model.game.conditions import QueryResolutionError
from model.game.snapshot_queries import SnapshotQueries


def test_snapshot_queries_do_not_expose_mutable_session_state():
    original = {
        "rule_state": {"tokens": [{"owner": "white", "id": 1}]},
        "special_rights": {"castle_short": True},
        "temporary_targets": {"en_passant": None},
    }
    queries = SnapshotQueries(original)
    original["rule_state"]["tokens"][0]["owner"] = "black"
    result = queries.rule_state({"name": "tokens"})
    assert result == [{"owner": "white", "id": 1}]
    result[0]["owner"] = "black"
    assert queries.rule_state({"name": "tokens"}) == [{"owner": "white", "id": 1}]
    assert queries.special_rights({"name": "castle_short"}) is True
    assert queries.temporary_target({"name": "en_passant"}) is None


@pytest.mark.parametrize(
    "payload",
    [
        {"rule_state": {"x": object()}},
        {"rule_state": {"x": float("nan")}},
        {"rule_state": {"x": (1, 2)}},
    ],
)
def test_snapshot_rejects_executable_or_non_json_data(payload):
    with pytest.raises(QueryResolutionError):
        SnapshotQueries(payload)


def test_unknown_or_unbound_snapshot_facts_fail_closed():
    queries = SnapshotQueries({"rule_state": {"counter": 2}})
    assert queries.rule_state({"name": "counter"}) == 2
    with pytest.raises(QueryResolutionError):
        queries.rule_state({"name": "missing"})
    with pytest.raises(QueryResolutionError):
        queries.rule_state({"name": "counter", "extra": True})
    with pytest.raises(QueryResolutionError):
        queries.clock_remaining({"side": "active"})


def test_versioned_rule_program_reads_trusted_snapshot_without_mutating_it():
    from model.game.hooks import RuleProgram

    source = {"rule_state": {"can_move": True}}
    reader = SnapshotQueries(source)
    rule = {
        "id": "allow-when-authorized",
        "hook": "permits_move",
        "when": {
            "op": "compare",
            "relation": "eq",
            "left": {"query": "rule_state", "params": {"name": "can_move"}},
            "right": True,
        },
        "effects": [{"op": "permit", "params": {}}],
    }
    program = RuleProgram([rule])
    accepted = program.evaluate("permits_move", {"rule_state": reader.rule_state})
    assert [effect.op for effect in accepted.effects] == ["permit"]
    assert source["rule_state"]["can_move"] is True
    blocked = SnapshotQueries({"rule_state": {"can_move": False}})
    rejected = program.evaluate("permits_move", {"rule_state": blocked.rule_state})
    assert rejected.effects == ()
    assert source["rule_state"]["can_move"] is True
