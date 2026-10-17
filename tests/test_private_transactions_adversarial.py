"""Independent FR-80 adversarial consumers of genuine private PostgreSQL commits."""

from copy import deepcopy
import json
from uuid import uuid4

import pytest

from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager
from engine.model.game.move import Move
from test_private_transactions import Session, active, literal, pending, postgres


def test_same_text_action_key_is_independent_across_all_lifecycle_namespaces(
    pending: Session,
) -> None:
    """FR-80: creation, activation and an actual move have distinct idempotency scopes."""
    assert pending.db.sql(pending.activate_sql(action="create"), role="service_role") == "0"
    state, event = pending.first_action("create")
    assert pending.db.sql(pending.commit_sql(state, event), role="service_role") == "1"
    before = pending.stored()
    assert before["game"]["create_action_id"] == "create"
    assert [(record["action_scope"], record["action_id"]) for record in before["events"]] == [
        ("activation", "create"),
        ("domain", "create"),
    ]
    assert pending.db.sql(pending.commit_sql(state, event), role="service_role") == "1"
    assert pending.stored() == before
    assert GameManager.from_snapshot(before["game"]["state"]).get_state() == state


def test_sql_syntax_in_action_identifier_remains_data_and_preserves_unrelated_records(
    active: Session,
) -> None:
    """FR-80: opaque keyed actions cannot turn provider data into SQL execution."""
    action = "join'; DELETE FROM retained_records.protected_data; --"
    state, event = active.first_action(action)
    assert active.db.sql(active.commit_sql(state, event), role="service_role") == "1"
    stored = active.stored()
    assert stored["events"][-1]["action_id"] == action
    assert stored["game"]["state"] == state
    assert active.db.sql("select value from retained_records.protected_data") == "preserved"
    assert active.db.sql(active.commit_sql(state, event), role="service_role") == "1"
    assert active.stored() == stored


def test_known_action_retry_never_authorizes_an_outsider_or_another_participant(
    active: Session,
) -> None:
    """FR-80: idempotency cannot replace participant identity checks."""
    state, event = active.first_action("known")
    active.db.sql(active.commit_sql(state, event), role="service_role")
    before = active.stored()
    active.db.reject(active.commit_sql(state, event, actor=active.identities[2]), "42501")
    assert active.stored() == before
    active.db.reject(active.commit_sql(state, event, actor=active.identities[1]), "23505")
    assert active.stored() == before


@pytest.mark.parametrize(
    "path,value",
    [
        (("board", 0, "side"), True),
        (("board", 0, "moved"), 1),
        (("board", 0, "square", 0), 2.0),
        (("clocks", "remaining_ms", "1"), 59900.0),
        (("clocks", "anchor_ms"), True),
    ],
)
def test_commit_rejects_scalar_alias_corruption_without_transaction_side_effects(
    active: Session, path: tuple, value
) -> None:
    """FR-80: typed board and clock metadata cannot exploit JSON numeric coercion."""
    before = active.stored()
    state, event = active.first_action()
    corrupted = deepcopy(state)
    target = corrupted
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    active.db.reject(active.commit_sql(corrupted, event), "22023")
    assert active.stored() == before
    assert active.db.sql(active.commit_sql(state, event), role="service_role") == "1"
    assert active.stored()["game"]["state"] == state


def test_terminal_engine_result_cannot_be_erased_by_a_new_database_action(pending: Session) -> None:
    """FR-80: a persisted terminal result prevents further transitions and survives retry."""
    config = deepcopy(pending.config)
    config["rules"].append(
        {
            "id": "terminal",
            "hook": "outcome",
            "when": {"op": "true"},
            "effects": [
                {
                    "op": "propose_outcome",
                    "params": {"kind": "draw", "cause": "declared", "winner": None, "priority": 1},
                }
            ],
        }
    )
    identifier = str(uuid4())
    engine = GameManager(validate_definition(config), identifier, pending.identities[:2], 1000)
    fixture = Session(
        pending.db, identifier, pending.identities, engine, engine.get_state()["config"]
    )
    assert (
        fixture.db.sql(fixture.create_sql(action="terminal-create"), role="service_role")
        == identifier
    )
    assert fixture.db.sql(fixture.activate_sql(), role="service_role") == "0"
    state, event = fixture.first_action("terminal-move")
    assert state["outcome"]["kind"] == "draw"
    assert fixture.db.sql(fixture.commit_sql(state, event), role="service_role") == "1"
    before = fixture.stored()
    next_state = deepcopy(state)
    next_state.update(revision=2, active_side=1, outcome=None)
    second = {
        "revision": 2,
        "expected_revision": 1,
        "actor": fixture.identities[1],
        "action_id": "after-terminal",
        "at_ms": 1200,
        "move": Move((0, 3), (1, 2)).to_json(),
        "captured": [],
        "effects": [],
        "outcome": None,
    }
    next_state["clocks"]["anchor_ms"] = 1200
    next_state["events"].append(second)
    fixture.db.reject(
        fixture.commit_sql(next_state, second, actor=fixture.identities[1], expected=1), "55000"
    )
    assert fixture.stored() == before
    assert fixture.db.sql(fixture.commit_sql(state, event), role="service_role") == "1"
    assert fixture.stored() == before
    assert GameManager.from_snapshot(before["game"]["state"]).get_state() == state


def test_database_reload_and_later_retry_do_not_require_historical_process_memory(
    active: Session,
) -> None:
    """FR-80: reconstruct public state from committed data before handling an old retry."""
    first_state, first = active.first_action("first")
    active.db.sql(active.commit_sql(first_state, first), role="service_role")
    second = active.engine.submit(active.identities[1], 1, "second", Move((0, 3), (1, 2)), 1200)
    active.db.sql(
        active.commit_sql(
            active.engine.get_state(), second, actor=active.identities[1], expected=1
        ),
        role="service_role",
    )
    durable = active.stored()
    snapshot = json.loads(
        active.db.sql(
            f"select state from bgwq.games where id={literal(active.game)}", role="service_role"
        )
    )
    restarted = GameManager.from_snapshot(snapshot)
    retry = restarted.submit(active.identities[0], 0, "first", Move((3, 0), (2, 1)), 99999)
    assert retry == first
    assert restarted.get_state() == snapshot
    assert snapshot["revision"] == 2
    assert active.stored() == durable
    active.db.reject(active.commit_sql(snapshot, retry), "23505")
    assert active.stored() == durable
