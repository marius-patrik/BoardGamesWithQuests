"""G2/G4 terminal SQL contract through genuine engine outputs and PostgreSQL.

Run with the integrated terminal engine on PYTHONPATH. The SQL role is a trusted
server consumer, not proof of hosted JWT/HTTP authorization.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier
from uuid import uuid4

import pytest

from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager
from engine.model.game.move import Move
from test_private_transactions import Session, literal, pending, postgres  # noqa: F401


@pytest.fixture
def terminal(pending, request):
    """Configure all results as data; use a nonzero increment to detect credit."""
    config = deepcopy(pending.config)
    config["starting_side"] = getattr(request, "param", 1)
    config["clock"] = {"initial_seconds": 1, "increment_seconds": 2}
    for command, kind, winner in (
        ("resign", "win", {"ref": "player.opponent.id"}),
        ("timeout", "win", {"ref": "turn.opponent.id"}),
        ("claim_draw", "draw", None),
    ):
        # Literal side -1 is the inactive side in this fixture. Engine resolves
        # the side to the actual participant; SQL receives no client winner.
        if command == "timeout":
            winner = -config["starting_side"]
        config["rules"].append(
            {
                "id": command,
                "hook": "outcome",
                "when": {
                    "op": "compare",
                    "relation": "eq",
                    "left": {"ref": "event.type"},
                    "right": command,
                },
                "effects": [
                    {
                        "op": "propose_outcome",
                        "params": {
                            "kind": kind,
                            "cause": command,
                            "winner": winner,
                            "priority": 10,
                        },
                    }
                ],
            }
        )
    game = str(uuid4())
    engine = GameManager(validate_definition(config), game, pending.identities[:2], 1000)
    session = Session(pending.db, game, pending.identities, engine, engine.get_state()["config"])
    session.db.sql(session.create_sql(action=game), role="service_role")
    session.db.sql(session.activate_sql(), role="service_role")
    return session


def action(command, intended=None):
    if command == "claim_draw":
        return {"type": command, "claim": command, "intended_move": intended}
    return {"type": command}


def prepare(session, command="resign", actor=0, at=1100, intended=None):
    event = session.engine.submit_action(
        session.identities[actor], 0, "terminal", action(command, intended), at
    )
    return session.engine.get_state(), event


@pytest.mark.parametrize(
    "command,actor,at",
    [
        ("resign", 0, 1100),
        ("resign", 1, 1100),
        ("resign", 1, 2100),
        ("timeout", 0, 2000),
        ("timeout", 1, 2100),
        ("claim_draw", 0, 1999),
    ],
)
def test_terminal_commit_clocks_restart_and_exact_retry(terminal, command, actor, at):
    """FR-11/50/63/69: preserve position, charge only active clock, recover."""
    initial = terminal.engine.get_state()
    state, event = prepare(terminal, command, actor, at)
    request = terminal.commit_sql(state, event, actor=terminal.identities[actor])
    assert terminal.db.sql(request, role="service_role") == "1"
    durable = terminal.stored()
    assert durable["game"]["state"] == state
    assert len(durable["events"]) == 2
    assert state["clocks"]["remaining_ms"] == {"1": max(0, 2000 - at), "-1": 1000}
    assert state["clocks"]["anchor_ms"] == at
    for field in (
        "board",
        "captured",
        "rule_state",
        "special_rights",
        "temporary_targets",
        "quest_progress",
        "halfmove_count",
        "position_history",
        "active_side",
    ):
        assert state[field] == initial[field]
    recovered = GameManager.from_snapshot(durable["game"]["state"])
    assert recovered.get_state() == state
    assert (
        recovered.submit_action(terminal.identities[actor], 0, "terminal", action(command), 99999)
        == event
    )
    assert terminal.db.sql(request, role="service_role") == "1"
    assert terminal.stored() == durable
    changed = deepcopy(state)
    changed["clocks"]["anchor_ms"] += 1
    terminal.db.reject(
        terminal.commit_sql(changed, event, actor=terminal.identities[actor]), "23505"
    )
    later = deepcopy(event)
    later["action_id"] = "later"
    terminal.db.reject(
        terminal.commit_sql(state, later, actor=terminal.identities[actor], expected=1), "55000"
    )
    assert terminal.stored() == durable


def test_projected_claim_does_not_persist_intended_move(terminal):
    """FR-16: a legal claim probe is data, never a board transition."""
    intended = Move((3, 0), (2, 1)).to_json()
    initial = terminal.engine.get_state()
    state, event = prepare(terminal, "claim_draw", intended=intended)
    assert terminal.db.sql(terminal.commit_sql(state, event), role="service_role") == "1"
    assert state["board"] == initial["board"] and event["move"] is None
    assert GameManager.from_snapshot(terminal.stored()["game"]["state"]).get_state() == state


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("outsider", "42501"),
        ("claim_inactive", "42501"),
        ("early_timeout", "22023"),
        ("expired_claim", "22023"),
        ("unknown", "22023"),
        ("winner_assertion", "22023"),
        ("time_assertion", "22023"),
        ("missing_action", "22023"),
        ("claim_unknown", "22023"),
        ("claim_missing_intent", "22023"),
        ("claim_bad_intent", "22023"),
        ("null_action", "22023"),
        ("move", "22023"),
        ("captured", "22023"),
        ("effects", "22023"),
        ("winner", "22023"),
        ("wrong_winner", "22023"),
        ("cause", "22023"),
        ("priority", "22023"),
        ("outcome", "22023"),
        ("actor", "22023"),
        ("stale", "40001"),
        ("backwards", "22023"),
        ("clock_active", "22023"),
        ("clock_inactive", "22023"),
        ("anchor", "22023"),
        ("increment", "22023"),
        ("board", "22023"),
        ("rule_state", "22023"),
        ("special_rights", "22023"),
        ("temporary_targets", "22023"),
        ("quest_progress", "22023"),
        ("halfmove_count", "22023"),
        ("position_history", "22023"),
        ("active_side", "22023"),
        ("config", "22023"),
        ("participants", "22023"),
    ],
)
def test_terminal_rejections_are_atomic(terminal, mutation, code):
    """G4: malformed assertions and unauthorized actions leave all rows intact."""
    before = terminal.stored()
    state, event = prepare(terminal)
    actor, expected = terminal.identities[0], 0
    if mutation == "outsider":
        actor = terminal.identities[2]
    elif mutation == "stale":
        expected = 1
    elif mutation == "claim_inactive":
        actor = terminal.identities[1]
        event["actor"] = actor
        event["action"] = action("claim_draw")
    elif mutation == "early_timeout":
        event["action"] = action("timeout")
    elif mutation == "expired_claim":
        event["action"] = action("claim_draw")
        event["at_ms"] = 2000
        state["clocks"]["anchor_ms"] = 2000
        state["clocks"]["remaining_ms"]["1"] = 0
    elif mutation == "unknown":
        event["action"] = {"type": "agree_draw"}
    elif mutation in ("winner_assertion", "time_assertion"):
        event["action"]["winner" if mutation == "winner_assertion" else "at_ms"] = actor
    elif mutation == "missing_action":
        del event["action"]
    elif mutation == "null_action":
        event["action"] = None
    elif mutation.startswith("claim_"):
        event["action"] = action("claim_draw")
        if mutation == "claim_unknown":
            event["action"]["claim"] = "unknown"
        elif mutation == "claim_missing_intent":
            del event["action"]["intended_move"]
        else:
            event["action"]["intended_move"] = {"start": [3, 0], "hops": [], "promotion": None}
    elif mutation == "move":
        event["move"] = Move((3, 0), (2, 1)).to_json()
    elif mutation in ("captured", "effects"):
        event[mutation] = [None]
    elif mutation in ("winner", "cause", "priority"):
        state["outcome"][mutation] = {
            "winner": terminal.identities[2],
            "cause": "unknown",
            "priority": 999,
        }[mutation]
        event["outcome"] = deepcopy(state["outcome"])
    elif mutation == "wrong_winner":
        state["outcome"]["winner"] = actor
        event["outcome"] = deepcopy(state["outcome"])
    elif mutation == "outcome":
        event["outcome"] = None
    elif mutation == "actor":
        event["actor"] = terminal.identities[1]
    elif mutation == "backwards":
        event["at_ms"] = 999
    elif mutation in ("clock_active", "clock_inactive"):
        state["clocks"]["remaining_ms"]["1" if mutation == "clock_active" else "-1"] += 1
    elif mutation in ("anchor", "increment"):
        state["clocks"][mutation + "_ms"] += 1
    elif mutation == "board":
        state["board"][0]["moved"] = True
    elif mutation == "halfmove_count":
        state[mutation] += 1
    elif mutation == "active_side":
        state[mutation] *= -1
    elif mutation == "config":
        state["config"]["clock"]["initial_seconds"] += 1
    elif mutation == "participants":
        state[mutation]["-1"] = terminal.identities[2]
    elif mutation == "position_history":
        state[mutation].append("forged")
    else:
        state[mutation]["forged"] = 1
    state["events"][-1] = deepcopy(event)
    terminal.db.reject(terminal.commit_sql(state, event, actor=actor, expected=expected), code)
    assert terminal.stored() == before


def test_later_move_retry_after_terminal_is_idempotent(terminal):
    """G4: accepted move retries precede stale/terminal rejection after restart."""
    first_state, first = terminal.first_action()
    first_request = terminal.commit_sql(first_state, first)
    terminal.db.sql(first_request, role="service_role")
    event = terminal.engine.submit_action(
        terminal.identities[0], 1, "resign", action("resign"), 1200
    )
    state = terminal.engine.get_state()
    terminal.db.sql(terminal.commit_sql(state, event, expected=1), role="service_role")
    before = terminal.stored()
    assert terminal.db.sql(first_request, role="service_role") == "1"
    recovered = GameManager.from_snapshot(before["game"]["state"])
    assert recovered.submit(terminal.identities[0], 0, "move", Move((3, 0), (2, 1)), 99999) == first
    assert terminal.stored() == before


def test_terminal_insert_failure_rolls_back(terminal):
    """G4: event failure rolls back the snapshot and clock charge."""
    state, event = prepare(terminal)
    before = terminal.stored()
    name = "fault_" + uuid4().hex
    terminal.db.sql(f"""
      create function bgwq.{name}() returns trigger language plpgsql as $$
      begin if new.game_id={literal(terminal.game)}::uuid then raise exception 'terminal fault'; end if; return new; end $$;
      create trigger {name} before insert on bgwq.events for each row execute function bgwq.{name}();
    """)
    try:
        terminal.db.reject(terminal.commit_sql(state, event), "P0001")
        assert terminal.stored() == before
    finally:
        terminal.db.sql(f"drop trigger {name} on bgwq.events; drop function bgwq.{name}();")


@pytest.mark.parametrize("competitor", ["move", "terminal", "retry"])
def test_concurrent_terminal_serialization(terminal, competitor):
    """G4: competing requests serialize; exact concurrent retries share one event."""
    other = GameManager.from_snapshot(terminal.engine.get_state())
    state, event = prepare(terminal)
    first = terminal.commit_sql(state, event)
    if competitor == "retry":
        second = first
    elif competitor == "move":
        move = other.submit(terminal.identities[0], 0, "move", Move((3, 0), (2, 1)), 1100)
        second = terminal.commit_sql(other.get_state(), move)
    else:
        rival = other.submit_action(terminal.identities[1], 0, "rival", action("resign"), 1100)
        second = terminal.commit_sql(other.get_state(), rival, actor=terminal.identities[1])
    barrier = Barrier(2)

    def commit(request):
        barrier.wait()
        return terminal.db.run("begin;\n" + request + ";\ncommit;", role="service_role")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(commit, [first, second]))
    assert sum(r.returncode == 0 for r in results) == (2 if competitor == "retry" else 1)
    for result in results:
        if result.returncode:
            assert "40001" in result.stderr
    durable = terminal.stored()
    assert durable["game"]["revision"] == 1 and len(durable["events"]) == 2
    assert (
        GameManager.from_snapshot(durable["game"]["state"]).get_state() == durable["game"]["state"]
    )


@pytest.mark.parametrize("terminal", [-1, 1], indirect=True)
@pytest.mark.parametrize("command", ["resign", "timeout", "claim_draw"])
def test_terminal_pinned_opening_side(terminal, command):
    """G2/G4: configured opening side controls turn and charged clock."""
    side = terminal.config["starting_side"]
    actor = 0 if side == 1 else 1
    at = 2000 if command == "timeout" else 1100
    state, event = prepare(terminal, command, actor, at)
    assert (
        terminal.db.sql(
            terminal.commit_sql(state, event, actor=terminal.identities[actor]), role="service_role"
        )
        == "1"
    )
    assert state["active_side"] == side
    assert state["clocks"]["remaining_ms"][str(side)] == max(0, 2000 - at)
    assert state["clocks"]["remaining_ms"][str(-side)] == 1000
    assert GameManager.from_snapshot(terminal.stored()["game"]["state"]).get_state() == state


@pytest.mark.parametrize("claim", ["q" * 65536, "é" * 4096])
def test_configured_long_claim_identifier(terminal, claim):
    """G2/G4: claim IDs use the configuration byte envelope, not action-ID bounds."""
    config = deepcopy(terminal.config)
    config["rules"][-1]["id"] = claim
    game = str(uuid4())
    engine = GameManager(validate_definition(config), game, terminal.identities[:2], 1000)
    session = Session(terminal.db, game, terminal.identities, engine, engine.get_state()["config"])
    session.db.sql(session.create_sql(action=game), role="service_role")
    session.db.sql(session.activate_sql(), role="service_role")
    event = engine.submit_action(
        session.identities[0],
        0,
        "claim",
        {"type": "claim_draw", "claim": claim, "intended_move": None},
        1100,
    )
    state = engine.get_state()
    assert session.db.sql(session.commit_sql(state, event), role="service_role") == "1"
    assert GameManager.from_snapshot(session.stored()["game"]["state"]).get_state() == state


def test_provider_terminal_probe_rolls_back_every_private_write(terminal):
    """Rehearse the same provider SQL and preserve all pre-existing data."""
    from pathlib import Path

    before = terminal.db.sql(
        "select jsonb_build_array((select count(*) from bgwq.games),(select count(*) from bgwq.events),(select count(*) from auth.users))"
    )
    probe = Path(__file__).parents[1] / "scripts/fixtures/provider_terminal_atomicity.sql"
    assert "draw claim and rollback probe passed" in terminal.db.sql(probe.read_text())
    assert (
        terminal.db.sql(
            "select jsonb_build_array((select count(*) from bgwq.games),(select count(*) from bgwq.events),(select count(*) from auth.users))"
        )
        == before
    )
    assert terminal.db.sql("select value from retained_records.protected_data") == "preserved"
