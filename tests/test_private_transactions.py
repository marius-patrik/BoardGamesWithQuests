"""Real PostgreSQL lifecycle transactions; hosted Auth/HTTP acceptance is separate.

The isolated database uses the same private migrations and restrictive Supabase
roles. Its Auth fixture supplies FK identities only, never authentication proof.
Failure to start PostgreSQL blocks this mandatory gate rather than skipping it.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
from threading import Barrier
import time
from typing import Any
from uuid import uuid4

import pytest

from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move

ROOT = Path(__file__).resolve().parents[1]
POSTGRES_IMAGE = "postgres@sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685"
MIGRATIONS = (
    "20261013145509_private_game_persistence.sql",
    "20261013151643_immutable_game_snapshot.sql",
    "20261013192000_isolate_unrelated_records.sql",
    "20261013202238_private_session_lifecycle.sql",
)


def literal(value: Any) -> str:
    """Encode SQL data safely without interpolating identifiers or shell commands."""
    if value is None:
        return "null"
    text = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
    return "'" + text.replace("'", "''") + "'"


@dataclass
class Postgres:
    """A genuine isolated PostgreSQL server reached through psql."""

    container: str

    def run(self, sql: str, *, role: str | None = None) -> subprocess.CompletedProcess[str]:
        """Execute one SQL consumer request on an independent database connection."""
        if role is not None:
            assert role in {"service_role", "anon", "authenticated"}
            sql = f"set role {role};\n" + sql
        return subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                self.container,
                "psql",
                "-X",
                "-q",
                "-A",
                "-t",
                "-h",
                "127.0.0.1",
                "-U",
                "postgres",
                "-v",
                "ON_ERROR_STOP=1",
                "-v",
                "VERBOSITY=verbose",
            ],
            input=sql,
            text=True,
            capture_output=True,
            check=False,
        )

    def sql(self, sql: str, *, role: str | None = None) -> str:
        """Require successful execution and return the committed query response."""
        result = self.run(sql, role=role)
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    def reject(self, sql: str, code: str, *, role: str = "service_role") -> None:
        """Assert a real database rejection with the expected SQLSTATE."""
        result = self.run(sql, role=role)
        assert result.returncode != 0 and f"ERROR:  {code}:" in result.stderr, result.stderr


@pytest.fixture(scope="session")
def postgres() -> Postgres:
    """Start a disposable server and install only the application's private schema."""
    if shutil.which("docker") is None:
        pytest.fail("PostgreSQL integration gate blocked: Docker is unavailable")
    container = f"bgwq-sql-tests-{uuid4().hex}"
    started = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            container,
            "-e",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            POSTGRES_IMAGE,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if started.returncode != 0:
        pytest.fail(f"PostgreSQL integration gate blocked: {started.stderr}")
    db = Postgres(container)
    try:
        for _ in range(100):
            ready = subprocess.run(
                ["docker", "exec", container, "pg_isready", "-h", "127.0.0.1", "-U", "postgres"],
                capture_output=True,
                check=False,
            )
            if ready.returncode == 0:
                break
            time.sleep(0.1)
        else:
            pytest.fail("PostgreSQL integration gate blocked: server did not become ready")
        db.sql("""
          create role anon; create role authenticated; create role service_role bypassrls;
          create schema auth; create table auth.users(id uuid primary key);
          grant usage on schema auth to service_role;
          create table public.accounts(value text not null);
          create table public.wallets(value text not null);
          create table public.game_stats(value text not null);
          insert into public.accounts values ('account-preserved');
          insert into public.wallets values ('wallet-preserved');
          insert into public.game_stats values ('stats-preserved');
          grant select on public.accounts, public.wallets, public.game_stats to anon, authenticated;
          create schema retained_records;
          create table retained_records.protected_data(value text not null);
          insert into retained_records.protected_data values ('preserved');
        """)
        for migration in MIGRATIONS:
            db.sql(
                "begin;\n" + (ROOT / "supabase/migrations" / migration).read_text() + "\ncommit;"
            )
        assert db.sql("select value from retained_records.protected_data") == "preserved"
        yield db
    finally:
        subprocess.run(["docker", "stop", container], capture_output=True, check=False)


@dataclass
class Session:
    """Real engine-generated snapshots supplied to the private SQL boundary."""

    db: Postgres
    game: str
    identities: tuple[str, str, str]
    engine: GameManager
    config: dict[str, Any]

    def create_sql(self, action: str = "create", config: dict | None = None) -> str:
        """Prepare a stable keyed creation call."""
        return f"select bgwq.create_game({literal(self.game)}, {literal(self.identities[0])}, {literal(action)}, {literal(self.config if config is None else config)}::jsonb)"

    def activate_sql(
        self, *, actor: str | None = None, action: str = "join", state: dict | None = None
    ) -> str:
        """Prepare a participant-bound genesis activation call."""
        return f"select bgwq.activate_game({literal(self.game)}, {literal(actor or self.identities[1])}, {literal(action)}, {literal(self.engine.get_state() if state is None else state)}::jsonb)"

    def commit_sql(
        self, state: dict, event: dict, *, actor: str | None = None, expected: int = 0
    ) -> str:
        """Prepare an immutable engine event and resulting snapshot commit."""
        return f"select bgwq.commit_revision({literal(self.game)}, {literal(actor or self.identities[0])}, {expected}, {literal(state)}::jsonb, {literal(event)}::jsonb)"

    def stored(self) -> dict[str, Any]:
        """Read committed row and events for complete no-side-effect assertions."""
        return json.loads(self.db.sql(f"""
          select jsonb_build_object('game',to_jsonb(g), 'events',
            coalesce((select jsonb_agg(to_jsonb(e) order by revision) from bgwq.events e where e.game_id=g.id), '[]'::jsonb))
          from bgwq.games g where id={literal(self.game)}
        """))

    def first_action(self, action: str = "move") -> tuple[dict, dict]:
        """Execute an actual legal generic engine intent and capture its outputs."""
        event = self.engine.submit(self.identities[0], 0, action, Move((3, 0), (2, 1)), 1100)
        return self.engine.get_state(), event


@pytest.fixture
def pending(postgres: Postgres) -> Session:
    """Create a pending game with genuine local FK identities and validated JSON."""
    identities = tuple(str(uuid4()) for _ in range(3))
    postgres.sql(
        "insert into auth.users(id) values " + ",".join(f"({literal(x)})" for x in identities)
    )
    data = json.loads((ROOT / "packages/english_draughts/config.json").read_text())
    data["name"] = "private-transaction-fixture"
    data["starting_side"] = 1
    data["board"] = {
        "rows": 4,
        "columns": 4,
        "starting_pieces": [
            {"piece": "man", "color": "white", "squares": [[3, 0]]},
            {"piece": "man", "color": "black", "squares": [[0, 3]]},
        ],
    }
    data["rules"] = [
        {
            "id": "explicit_permission",
            "hook": "permits_move",
            "when": {"op": "true"},
            "effects": [{"op": "permit", "params": {}}],
        }
    ]
    data["quests"] = []
    data["clock"] = {"initial_seconds": 60, "increment_seconds": 0}
    game = str(uuid4())
    engine = GameManager(validate_definition(data), game, identities[:2], 1000)
    session = Session(postgres, game, identities, engine, engine.get_state()["config"])
    assert postgres.sql(session.create_sql(), role="service_role") == game
    return session


@pytest.fixture
def active(pending: Session) -> Session:
    """Activate exactly two authenticated UUID references at domain revision zero."""
    assert pending.db.sql(pending.activate_sql(), role="service_role") == "0"
    return pending


def test_create_retry_is_idempotent_and_genesis_does_not_enter_domain_history(
    pending: Session,
) -> None:
    before = pending.stored()
    assert pending.db.sql(pending.create_sql(), role="service_role") == pending.game
    assert pending.stored() == before
    assert before["game"]["player_two"] is None and before["game"]["state"] == {}
    assert before["events"] == []
    assert pending.db.sql(pending.activate_sql(), role="service_role") == "0"
    stored = pending.stored()
    assert stored["game"]["revision"] == 0 and stored["game"]["state"]["events"] == []
    assert len(stored["events"]) == 1 and stored["events"][0]["revision"] == 0
    assert stored["events"][0]["payload"]["kind"] == "activation"
    assert (
        GameManager.from_snapshot(stored["game"]["state"]).get_state() == pending.engine.get_state()
    )


@pytest.mark.parametrize("mutation", ["config", "game", "malformed", "missing_identity"])
def test_conflicting_or_invalid_creation_leaves_existing_game_unchanged(
    pending: Session, mutation: str
) -> None:
    before = pending.stored()
    config = deepcopy(pending.config)
    if mutation == "config":
        config["title"] = "different"
        sql, code = pending.create_sql(config=config), "23505"
    elif mutation == "game":
        sql, code = pending.create_sql().replace(pending.game, str(uuid4())), "23505"
    elif mutation == "malformed":
        sql, code = pending.create_sql(config={"schema_version": True}), "22023"
    else:
        sql, code = (
            pending.create_sql(action="unknown")
            .replace(pending.identities[0], str(uuid4()))
            .replace(pending.game, str(uuid4())),
            "23503",
        )
    pending.db.reject(sql, code)
    assert pending.stored() == before


def test_activation_retry_survives_later_moves_and_rejects_conflicting_reuse(
    active: Session,
) -> None:
    initial = active.engine.get_state()
    state, event = active.first_action()
    assert active.db.sql(active.commit_sql(state, event), role="service_role") == "1"
    before = active.stored()
    assert active.db.sql(active.activate_sql(state=initial), role="service_role") == "0"
    assert active.db.sql(active.create_sql(), role="service_role") == active.game
    assert active.stored() == before
    corrupt = deepcopy(initial)
    corrupt["clocks"]["anchor_ms"] += 1
    active.db.reject(active.activate_sql(state=corrupt), "23505")
    active.db.reject(active.activate_sql(action="another"), "55000")
    assert active.stored() == before


def test_two_competing_joiners_fill_exactly_one_slot(pending: Session) -> None:
    barrier = Barrier(2)
    alternate = GameManager(
        pending.engine.definition,
        pending.game,
        (pending.identities[0], pending.identities[2]),
        1000,
    )
    requests = [
        pending.activate_sql(),
        pending.activate_sql(
            actor=pending.identities[2], action="other", state=alternate.get_state()
        ),
    ]

    def join(sql: str) -> subprocess.CompletedProcess[str]:
        barrier.wait()
        return pending.db.run("begin;\n" + sql + ";\ncommit;", role="service_role")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(join, requests))
    assert sum(result.returncode == 0 for result in results) == 1
    stored = pending.stored()
    assert stored["game"]["player_two"] in pending.identities[1:]
    assert stored["game"]["state"]["participants"]["-1"] == stored["game"]["player_two"]
    assert (
        len(stored["events"]) == 1 and stored["events"][0]["actor"] == stored["game"]["player_two"]
    )
    loser = next(
        identity for identity in pending.identities[1:] if identity != stored["game"]["player_two"]
    )
    pending.db.reject(
        pending.activate_sql(actor=loser, action="third", state=alternate.get_state()), "55000"
    )
    assert pending.stored() == stored


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("self", "42501"),
        ("identity", "23503"),
        ("participants", "22023"),
        ("boolean_revision", "22023"),
        ("string_revision", "22023"),
        ("config", "22023"),
        ("history", "22023"),
    ],
)
def test_invalid_join_cannot_mutate_pending_state(
    pending: Session, mutation: str, code: str
) -> None:
    before = pending.stored()
    actor = pending.identities[1]
    state = pending.engine.get_state()
    if mutation == "self":
        actor = pending.identities[0]
    elif mutation == "identity":
        actor = str(uuid4())
        state["participants"]["-1"] = actor
        state["quest_progress"][actor] = state["quest_progress"].pop(pending.identities[1])
    elif mutation == "participants":
        state["participants"]["1"] = pending.identities[2]
    elif mutation == "boolean_revision":
        state["revision"] = False
    elif mutation == "string_revision":
        state["revision"] = "0"
    elif mutation == "config":
        state["config"]["clock"]["initial_seconds"] = 61
    else:
        state["events"] = [{"revision": 1}]
    pending.db.reject(pending.activate_sql(actor=actor, state=state), code)
    assert pending.stored() == before


def test_commit_exact_retry_after_next_revision_preserves_history_and_restart(
    active: Session,
) -> None:
    first_state, first = active.first_action()
    assert active.db.sql(active.commit_sql(first_state, first), role="service_role") == "1"
    second = active.engine.submit(active.identities[1], 1, "second", Move((0, 3), (1, 2)), 1200)
    second_state = active.engine.get_state()
    assert (
        active.db.sql(
            active.commit_sql(second_state, second, actor=active.identities[1], expected=1),
            role="service_role",
        )
        == "2"
    )
    before = active.stored()
    assert active.db.sql(active.commit_sql(first_state, first), role="service_role") == "1"
    assert active.stored() == before
    assert [event["revision"] for event in before["events"]] == [0, 1, 2]
    assert GameManager.from_snapshot(before["game"]["state"]).get_state() == second_state


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("outsider", "42501"),
        ("wrong_turn", "42501"),
        ("stale", "40001"),
        ("participants", "22023"),
        ("config", "22023"),
        ("boolean_revision", "22023"),
        ("event_actor", "22023"),
        ("event_revision", "22023"),
        ("event_prefix", "22023"),
        ("move_claim", "22023"),
    ],
)
def test_invalid_commit_has_no_committed_side_effects(
    active: Session, mutation: str, code: str
) -> None:
    before = active.stored()
    state, event = active.first_action()
    actor, expected = active.identities[0], 0
    if mutation == "outsider":
        actor = active.identities[2]
    elif mutation == "wrong_turn":
        actor = active.identities[1]
    elif mutation == "stale":
        expected = 1
    elif mutation == "participants":
        state["participants"]["-1"] = active.identities[2]
    elif mutation == "config":
        state["config"]["clock"]["initial_seconds"] = 61
    elif mutation == "boolean_revision":
        state["revision"] = True
    elif mutation == "event_actor":
        event["actor"] = active.identities[1]
        state["events"][-1] = event
    elif mutation == "event_revision":
        event["revision"] = True
        state["events"][-1] = event
    elif mutation == "event_prefix":
        state["events"] = []
    else:
        event["move"]["captures"] = [[0, 3]]
        state["events"][-1] = event
    active.db.reject(active.commit_sql(state, event, actor=actor, expected=expected), code)
    assert active.stored() == before


def test_duplicate_and_conflicting_action_keys_are_atomic(active: Session) -> None:
    state, event = active.first_action()
    request = active.commit_sql(state, event)
    barrier = Barrier(2)

    def commit(_: int) -> subprocess.CompletedProcess[str]:
        barrier.wait()
        return active.db.run("begin;\n" + request + ";\ncommit;", role="service_role")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(commit, [0, 1]))
    assert all(result.returncode == 0 and result.stdout.strip() == "1" for result in results)
    before = active.stored()
    assert before["game"]["revision"] == 1 and len(before["events"]) == 2
    state["halfmove_count"] += 1
    active.db.reject(active.commit_sql(state, event), "23505")
    assert active.stored() == before


def test_competing_same_revision_moves_commit_only_once(active: Session) -> None:
    alternative = GameManager.from_snapshot(active.engine.get_state())
    state, first = active.first_action("one")
    second = alternative.submit(active.identities[0], 0, "two", Move((3, 0), (2, 1)), 1100)
    requests = [active.commit_sql(state, first), active.commit_sql(alternative.get_state(), second)]
    barrier = Barrier(2)

    def commit(sql: str) -> subprocess.CompletedProcess[str]:
        barrier.wait()
        return active.db.run("begin;\n" + sql + ";\ncommit;", role="service_role")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(commit, requests))
    assert sum(result.returncode == 0 for result in results) == 1
    assert any("40001" in result.stderr for result in results if result.returncode != 0)
    stored = active.stored()
    assert stored["game"]["revision"] == 1 and len(stored["events"]) == 2


@pytest.mark.parametrize("activation", [False, True])
def test_event_insert_failure_rolls_back_entire_transaction(
    pending: Session, activation: bool
) -> None:
    if not activation:
        pending.db.sql(pending.activate_sql(), role="service_role")
    before = pending.stored()
    function = "fault_" + uuid4().hex
    pending.db.sql(f"""
      create function bgwq.{function}() returns trigger language plpgsql as $$
      begin if new.game_id={literal(pending.game)}::uuid then raise exception 'injected event failure'; end if; return new; end $$;
      create trigger {function} before insert on bgwq.events for each row execute function bgwq.{function}();
    """)
    try:
        if activation:
            request = pending.activate_sql()
        else:
            state, event = pending.first_action()
            request = pending.commit_sql(state, event)
        pending.db.reject(request, "P0001")
        assert pending.stored() == before
    finally:
        pending.db.sql(f"drop trigger {function} on bgwq.events; drop function bgwq.{function}();")


@pytest.mark.parametrize(
    "field", ["config_snapshot", "player_one", "player_two", "create_action_id", "lifecycle"]
)
def test_active_identity_and_config_are_immutable(active: Session, field: str) -> None:
    before = active.stored()
    values = {
        "config_snapshot": "jsonb_set(config_snapshot, '{schema_version}', '2.0'::jsonb)",
        "player_one": literal(active.identities[2]) + "::uuid",
        "player_two": literal(active.identities[2]) + "::uuid",
        "create_action_id": "'replacement'",
        "lifecycle": "'pending'",
    }
    active.db.reject(
        f"update bgwq.games set {field}={values[field]} where id={literal(active.game)}", "23514"
    )
    assert active.stored() == before


def test_browser_roles_and_auth_record_reads_are_denied(active: Session) -> None:
    for role in ("anon", "authenticated"):
        active.db.reject(active.activate_sql(), "42501", role=role)
        active.db.reject(
            f"select state from bgwq.games where id={literal(active.game)}", "42501", role=role
        )
    active.db.reject("select id from auth.users", "42501")
    assert (
        active.db.sql(
            "select bool_and(relrowsecurity) from pg_class where oid in ('bgwq.games'::regclass,'bgwq.events'::regclass)"
        )
        == "t"
    )
    assert (
        active.db.sql(
            "select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='bgwq' and p.prosecdef"
        )
        == "0"
    )
    assert active.db.sql("select value from retained_records.protected_data") == "preserved"


@pytest.mark.parametrize(
    "field,value",
    [
        ("start", []),
        ("start", [3]),
        ("start", [True, 0]),
        ("start", [-1, 0]),
        ("start", [4, 0]),
        ("start", [3.0, 0]),
        ("hops", []),
        ("hops", [[2, 1]] * 129),
        ("hops", [[2]]),
        ("hops", [[False, 1]]),
        ("hops", [[2, 4]]),
        ("hops", [[3, 0]]),
        ("promotion", True),
        ("promotion", "unknown"),
        ("promotion", ""),
    ],
)
def test_malformed_move_dto_never_commits(active: Session, field: str, value: Any) -> None:
    """Wire-shape rejection is real SQL behavior, independently of game legality."""
    before = active.stored()
    state, event = active.first_action()
    event["move"][field] = value
    state["events"][-1] = deepcopy(event)
    active.db.reject(active.commit_sql(state, event), "22023")
    assert active.stored() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("action_id", None),
        ("action_id", True),
        ("action_id", ""),
        ("at_ms", True),
        ("at_ms", 1100.0),
        ("at_ms", -1),
        ("at_ms", 999),
        ("at_ms", 2**53),
        ("captured", {}),
        ("effects", None),
    ],
)
def test_malformed_event_metadata_never_commits(active: Session, field: str, value: Any) -> None:
    before = active.stored()
    state, event = active.first_action()
    event[field] = value
    state["events"][-1] = deepcopy(event)
    active.db.reject(active.commit_sql(state, event), "22023")
    assert active.stored() == before


def test_missing_event_field_and_mutable_clock_metadata_are_rejected(active: Session) -> None:
    before = active.stored()
    state, event = active.first_action()
    missing = deepcopy(event)
    del missing["outcome"]
    state["events"][-1] = missing
    active.db.reject(active.commit_sql(state, missing), "22023")
    state["events"][-1] = deepcopy(event)
    for field in ("anchor_ms", "increment_ms"):
        corrupted = deepcopy(state)
        corrupted["clocks"][field] += 1
        active.db.reject(active.commit_sql(corrupted, event), "22023")
    corrupted = deepcopy(state)
    corrupted["started_at_ms"] += 1
    active.db.reject(active.commit_sql(corrupted, event), "22023")
    assert active.stored() == before


def test_legacy_active_row_without_keyed_genesis_fails_closed(pending: Session) -> None:
    legacy = str(uuid4())
    state = pending.engine.get_state()
    state["game_id"] = legacy
    pending.db.sql(f"""
      insert into bgwq.games(id,player_one,player_two,config_snapshot,state)
      values ({literal(legacy)},{literal(pending.identities[0])},{literal(pending.identities[1])},
        {literal(pending.config)}::jsonb,{literal(state)}::jsonb)
    """)
    changed, event = pending.first_action()
    changed["game_id"] = legacy
    request = pending.commit_sql(changed, event).replace(pending.game, legacy)
    pending.db.reject(request, "55000")
    assert pending.db.sql(f"select revision from bgwq.games where id={literal(legacy)}") == "0"
    assert (
        pending.db.sql(f"select count(*) from bgwq.events where game_id={literal(legacy)}") == "0"
    )


def test_long_configured_promotion_identifier_is_accepted_as_database_metadata(
    pending: Session,
) -> None:
    """SQL supports the identifier bound; this does not certify domain promotion rules."""
    name = "p" * 128
    config = deepcopy(pending.config)
    config["pieces"][name] = deepcopy(config["pieces"]["man"])
    game = str(uuid4())
    manager = GameManager(validate_definition(config), game, pending.identities[:2], 1000)
    boundary = Session(pending.db, game, pending.identities, manager, manager.get_state()["config"])
    boundary.db.sql(boundary.create_sql(action="create-promotion"), role="service_role")
    boundary.db.sql(boundary.activate_sql(), role="service_role")
    state, event = boundary.first_action()
    # This is a trusted-state persistence contract fixture, not a legal promotion claim.
    event["move"]["promotion"] = name
    state["events"][-1] = deepcopy(event)
    assert boundary.db.sql(boundary.commit_sql(state, event), role="service_role") == "1"
    assert boundary.stored()["events"][-1]["payload"]["move"]["promotion"] == name


@pytest.mark.parametrize("action", ["create", "join"])
def test_domain_action_keys_do_not_collide_with_creation_or_activation(
    active: Session, action: str
) -> None:
    state, event = active.first_action(action)
    assert active.db.sql(active.commit_sql(state, event), role="service_role") == "1"
    stored = active.stored()
    assert active.db.sql(active.commit_sql(state, event), role="service_role") == "1"
    assert active.stored() == stored
    assert stored["events"][0]["action_scope"] == "activation"
    assert stored["events"][1]["action_scope"] == "domain"


def test_reconstructed_exact_retry_returns_accepted_event_and_latest_state_without_recommit(
    active: Session,
) -> None:
    """The future durable adapter must use this already-accepted detection contract."""
    first_state, first = active.first_action()
    active.db.sql(active.commit_sql(first_state, first), role="service_role")
    second = active.engine.submit(active.identities[1], 1, "next", Move((0, 3), (1, 2)), 1200)
    active.db.sql(
        active.commit_sql(
            active.engine.get_state(), second, actor=active.identities[1], expected=1
        ),
        role="service_role",
    )
    durable = active.stored()
    loaded = durable["game"]["state"]
    recovered = GameManager.from_snapshot(loaded)
    accepted = recovered.submit(active.identities[0], 0, "move", Move((3, 0), (2, 1)), 999999)
    assert accepted["revision"] <= loaded["revision"]
    response = {"event": accepted, "state": recovered.get_state()}
    assert response["event"] == first and response["state"]["revision"] == 2
    assert response["state"] == loaded and active.stored() == durable
    # Passing the latest snapshot with the old event is a conflicting low-level retry.
    active.db.reject(active.commit_sql(response["state"], response["event"]), "23505")
    assert active.stored() == durable


@pytest.mark.parametrize(
    "mutation",
    [
        "null_piece",
        "numeric_moved",
        "unknown_piece",
        "duplicate_square",
        "started_overflow",
        "clock",
        "anchor",
    ],
)
def test_corrupt_genesis_metadata_does_not_fill_participant_slot(
    pending: Session, mutation: str
) -> None:
    before = pending.stored()
    state = pending.engine.get_state()
    if mutation == "null_piece":
        state["board"][0] = None
    elif mutation == "numeric_moved":
        state["board"][0]["moved"] = 0
    elif mutation == "unknown_piece":
        state["board"][0]["kind"] = "unknown"
    elif mutation == "duplicate_square":
        state["board"].append(deepcopy(state["board"][0]))
    elif mutation == "started_overflow":
        state["started_at_ms"] = 2**53
    elif mutation == "clock":
        state["clocks"]["remaining_ms"]["1"] += 1
    else:
        state["clocks"]["anchor_ms"] += 1
    pending.db.reject(pending.activate_sql(state=state), "22023")
    assert pending.stored() == before


def test_provider_probe_rehearses_real_sql_and_rolls_back_all_test_objects(
    postgres: Postgres,
) -> None:
    """Local execution checks probe reproducibility, not hosted-provider acceptance."""
    postgres.sql(
        "insert into auth.users(id) values "
        + ",".join(f"({literal(str(uuid4()))})" for _ in range(3))
    )
    counts = postgres.sql(
        "select jsonb_build_array((select count(*) from auth.users),(select count(*) from bgwq.games),(select count(*) from bgwq.events))"
    )
    result = postgres.sql((ROOT / "scripts/fixtures/provider_session_atomicity.sql").read_text())
    assert "lifecycle, retry, authorization and rollback probe passed" in result
    assert (
        postgres.sql(
            "select jsonb_build_array((select count(*) from auth.users),(select count(*) from bgwq.games),(select count(*) from bgwq.events))"
        )
        == counts
    )
    assert postgres.sql("select count(*) from pg_proc where proname like 'provider_fault_%'") == "0"


@pytest.mark.parametrize("opening_side", [-1, 1])
def test_pinned_opening_side_uses_engine_genesis_and_authoritative_turn(
    pending: Session, opening_side: int
) -> None:
    """Persist the configured engine opening side and reject an unpinned genesis."""
    config = deepcopy(pending.config)
    config["starting_side"] = opening_side
    game = str(uuid4())
    manager = GameManager(validate_definition(config), game, pending.identities[:2], 1000)
    boundary = Session(pending.db, game, pending.identities, manager, manager.get_state()["config"])
    boundary.db.sql(boundary.create_sql(action="opening-" + game), role="service_role")
    genesis = manager.get_state()
    assert genesis["active_side"] == opening_side
    before = boundary.stored()
    incorrect = deepcopy(genesis)
    incorrect["active_side"] = -opening_side
    boundary.db.reject(boundary.activate_sql(state=incorrect), "22023")
    assert boundary.stored() == before
    assert boundary.db.sql(boundary.activate_sql(), role="service_role") == "0"
    participant = pending.identities[0 if opening_side == 1 else 1]
    intent = Move((3, 0), (2, 1)) if opening_side == 1 else Move((0, 3), (1, 2))
    event = manager.submit(participant, 0, "create", intent, 1100)
    state = manager.get_state()
    assert state["active_side"] == -opening_side
    assert (
        boundary.db.sql(boundary.commit_sql(state, event, actor=participant), role="service_role")
        == "1"
    )
    stored = boundary.stored()
    assert (
        boundary.db.sql(boundary.commit_sql(state, event, actor=participant), role="service_role")
        == "1"
    )
    assert boundary.stored() == stored
    recovered = GameManager.from_snapshot(stored["game"]["state"])
    assert recovered.submit(participant, 0, "create", intent, 999999) == event
    assert recovered.get_state() == state


@pytest.mark.parametrize("value", [True, False, 0, 2, "-1", None, 1.0])
def test_invalid_pinned_opening_side_cannot_create_game(pending: Session, value: Any) -> None:
    """Malformed opening-side metadata is rejected without durable effects."""
    config = deepcopy(pending.config)
    config["starting_side"] = value
    before = pending.stored()
    pending.db.reject(pending.create_sql(config=config, action="bad-opening"), "22023")
    assert pending.stored() == before


@pytest.mark.parametrize("role", ["anon", "authenticated"])
@pytest.mark.parametrize(
    "table,value",
    [
        ("accounts", "account-preserved"),
        ("wallets", "wallet-preserved"),
        ("game_stats", "stats-preserved"),
    ],
)
def test_full_migration_sequence_preserves_unrelated_rows_and_denies_browser(
    postgres, role, table, value
):
    """Apply actual record isolation before gameplay and preserve original data."""
    assert postgres.sql(f"select value from retained_records.{table}") == value
    postgres.reject(f"select * from retained_records.{table}", "42501", role=role)
    assert postgres.sql(f"select to_regclass('public.{table}') is null") == "t"


@pytest.mark.parametrize("fault", ["nodes", "depth"])
def test_activation_rejects_unrecoverable_document_without_durable_changes(pending, fault):
    """Reject documents beyond the engine recovery envelope before activation."""
    state = pending.engine.get_state()
    if fault == "nodes":
        state["position_history"] = [None] * 65537
    else:
        value = None
        for _ in range(34):
            value = {"nested": value}
        state["rule_state"] = value
    before = pending.stored()
    with pytest.raises((ValueError, TransitionError)):
        GameManager.from_snapshot(state)
    pending.db.reject(pending.activate_sql(state=state), "22023")
    assert pending.stored() == before
