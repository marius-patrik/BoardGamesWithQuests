"""Public data-only behavior of read-only authoritative snapshot queries."""

from __future__ import annotations

from copy import deepcopy

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


@pytest.mark.parametrize("payload", [
    {"rule_state": {"x": object()}},
    {"rule_state": {"x": float("nan")}},
    {"rule_state": {"x": (1, 2)}},
])
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
