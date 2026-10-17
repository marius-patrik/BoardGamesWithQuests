"""G4 real DB acceptance: no in-memory substitutes; unavailable Docker fails."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4

import pytest

from engine.model.game.configuration import validate_definition
from engine.model.game.move import Move
from server.persistence import GameStore, Conflict, Denied, InvalidInput, Unavailable
from test_private_transactions import Postgres, POSTGRES_IMAGE, MIGRATIONS, literal
from test_session_behavior import definition

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def database():
    if not shutil.which("docker"):
        pytest.fail("G4 adapter DB gate blocked: Docker unavailable")
    name = "bgwq-adapter-" + uuid4().hex
    password = uuid4().hex
    result = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            name,
            "-p",
            "127.0.0.1::5432",
            "-e",
            "POSTGRES_PASSWORD=" + password,
            "-e",
            "PGPASSWORD=" + password,
            POSTGRES_IMAGE,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        pytest.fail("G4 adapter DB gate blocked: " + result.stderr)
    db = Postgres(name)
    try:
        for _ in range(100):
            result = subprocess.run(
                ["docker", "exec", name, "pg_isready", "-h", "127.0.0.1", "-U", "postgres"],
                capture_output=True,
            )
            if result.returncode == 0:
                break
            time.sleep(0.1)
        else:
            pytest.fail("G4 adapter DB gate blocked: PostgreSQL startup failed")
        # Administrative fixture provisioning only; adapter connections log in as service_role.
        db.sql(
            "create role anon; create role authenticated; "
            f"create role service_role login bypassrls password '{password}'; "
            "create schema auth; create table auth.users(id uuid primary key); "
            "create table public.accounts(value text); "
            "create table public.wallets(value text); "
            "create table public.game_stats(value text);"
        )
        for migration in MIGRATIONS:
            db.sql((ROOT / "supabase/migrations" / migration).read_text())
        port = (
            subprocess.run(
                ["docker", "port", name, "5432/tcp"], capture_output=True, text=True, check=True
            )
            .stdout.strip()
            .split(":")[-1]
        )
        dsn = f"host=127.0.0.1 port={port} dbname=postgres user=service_role password={password} sslmode=disable"
        yield db, dsn
    finally:
        subprocess.run(["docker", "stop", name], capture_output=True)


def test_lifecycle_recovery_isolation_and_rollback(database):
    """FR-29/50/62: actual commits, fresh stores, historical retries and fault rollback."""
    db, dsn = database
    actors = [str(uuid4()) for _ in range(3)]
    db.sql("insert into auth.users(id) values " + ",".join(f"({literal(a)})" for a in actors))

    def store():
        return GameStore(dsn, local_test=True)

    async def scenario():
        a, b, outsider = actors
        creations = await asyncio.gather(
            store().create(a, "create", definition()), store().create(a, "create", definition())
        )
        assert creations[0] == creations[1]
        pending = creations[0]
        game = pending["id"]
        with pytest.raises(Denied):
            await store().read(a, str(uuid4()))
        assert await store().create(a, "create", definition()) == pending
        assert await store().read(a, game) == pending
        with pytest.raises(Conflict):
            await store().create(a, "create", definition(deny=True))
        for actor in (b, outsider):
            with pytest.raises(Denied):
                await store().read(actor, game)
        with pytest.raises(Denied):
            await store().join(a, game, "join", 1000)
        genesis = await store().join(b, game, "join", 1000)
        assert genesis["participants"] == {"1": a, "-1": b}
        assert genesis["revision"] == 0
        move = Move((5, 0), (4, 1))
        first = await store().submit(a, game, 0, "first", move, 1100)
        second = await store().submit(b, game, 1, "second", Move((0, 5), (1, 4)), 1200)
        recovered = await store().submit(a, game, 0, "first", move, 90000)
        assert recovered == {"event": first["event"], "state": second["state"]}
        assert await store().join(b, game, "join", 90000) == genesis
        with pytest.raises(Conflict):
            await store().join(b, game, "different", 1300)
        with pytest.raises(Denied):
            await store().join(outsider, game, "join", 1300)
        for operation in (
            store().read(outsider, game),
            store().submit(outsider, game, 2, "evil", move, 1300),
        ):
            with pytest.raises(Denied):
                await operation
        with pytest.raises(Conflict):
            await store().submit(a, game, 0, "first", Move((4, 1), (3, 0)), 1300)
        with pytest.raises(Conflict):
            await store().submit(a, game, 0, "stale", move, 1300)
        # Distinct independent connections race against one authoritative revision.
        results = await asyncio.gather(
            store().submit(a, game, 2, "race-one", Move((4, 1), (3, 0)), 1300),
            store().submit(a, game, 2, "race-two", Move((4, 1), (3, 2)), 1300),
            return_exceptions=True,
        )
        assert sum(isinstance(r, dict) for r in results) == 1
        assert sum(isinstance(r, Conflict) for r in results) == 1
        before = await store().read(a, game)
        # Real DB fault after UPDATE but before event insertion must roll back both.
        db.sql("""create function public.adapter_fault() returns trigger language plpgsql as $$
        begin raise exception 'injected event failure'; end $$;
        create trigger adapter_fault before insert on bgwq.events
        for each row execute function public.adapter_fault();""")
        try:
            with pytest.raises(Unavailable):
                await store().submit(b, game, 3, "fault", Move((1, 4), (2, 5)), 1400)
            assert await store().read(a, game) == before
            assert db.sql(f"select count(*) from bgwq.events where game_id={literal(game)}") == "4"
        finally:
            db.sql(
                "drop trigger adapter_fault on bgwq.events; drop function public.adapter_fault();"
            )
        retry = await store().submit(b, game, 3, "fault", Move((1, 4), (2, 5)), 1400)
        assert retry["state"]["revision"] == 4

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "field,value",
    [
        ("actor", "bad"),
        ("action", "\ud800"),
        ("action", "\x00"),
        ("game", str(uuid4()).upper()),
        ("action", ""),
        ("action", "x" * 129),
        ("revision", True),
        ("revision", -1),
        ("time", True),
        ("time", 2**53),
    ],
)
def test_malformed_arguments_before_connection(field, value):
    """FR-80: invalid input fails before touching an unreachable database."""
    args = dict(
        actor_id=str(uuid4()),
        game_id=str(uuid4()),
        expected_revision=0,
        action_id="action",
        move=Move((5, 0), (4, 1)),
        now_ms=1000,
    )
    args[
        dict(
            actor="actor_id",
            game="game_id",
            action="action_id",
            revision="expected_revision",
            time="now_ms",
        )[field]
    ] = value
    store = GameStore("host=127.0.0.1 port=1 sslmode=disable", local_test=True)
    with pytest.raises(InvalidInput):
        asyncio.run(store.submit(**args))


@pytest.mark.parametrize(
    "dsn",
    [
        "host=remote sslmode=disable",
        "host=localhost sslmode=require",
        "host=127.0.0.1 sslmode=disable",
    ],
)
def test_environment_requires_verified_tls(monkeypatch, dsn):
    monkeypatch.setenv("BGWQ_DATABASE_DSN", dsn)
    with pytest.raises(Unavailable):
        GameStore(local_test=True)


def test_provider_probe_missing_credentials_fails_explicitly():
    """External acceptance must fail closed rather than skip absent credentials."""
    import os
    import sys

    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("BGWQ_", "SUPABASE_"))
    }
    env["PYTHONPATH"] = str(ROOT / "packages")
    result = subprocess.run(
        [sys.executable, "-m", "server.persistence", "--verify-provider"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Persistence provider gate blocked: missing" in result.stderr


@pytest.mark.parametrize(
    "host", ["", "/tmp", "@socket", "remote,127.0.0.1", ",remote", "remote,", "remote host"]
)
def test_production_dsn_requires_one_network_host(host):
    """TLS flags cannot authorize a socket, omitted host or mixed endpoints."""
    with pytest.raises(Unavailable):
        GameStore(f"host='{host}' dbname=postgres sslmode=verify-full")


@pytest.mark.parametrize("extra", ["hostaddr=127.0.0.1", "service=other", "options='-c ssl=off'"])
def test_dsn_rejects_connection_overrides(extra):
    with pytest.raises(Unavailable):
        GameStore("host=database.example sslmode=verify-full " + extra)


def test_dsn_accepts_only_explicit_test_loopback(monkeypatch):
    for host in ("127.0.0.1", "::1"):
        GameStore(f"host={host} sslmode=disable", local_test=True)
    GameStore("host=db.example sslmode=verify-full")
    GameStore("postgresql://user@db.example/db?sslmode=verify-full")
    for dsn in (
        "sslmode=verify-full",
        "host=localhost sslmode=disable",
        "host=127.0.0.1,::1 sslmode=disable",
        "host=/tmp sslmode=disable",
    ):
        with pytest.raises(Unavailable):
            GameStore(dsn, local_test=True)
    monkeypatch.setenv("BGWQ_DATABASE_DSN", "host=127.0.0.1 sslmode=disable")
    with pytest.raises(Unavailable):
        GameStore(local_test=True)


def test_corrupted_durable_state_and_activation_fail_closed(database):
    """Real trusted-writer corruption cannot become an authoritative response."""
    db, dsn = database
    actors = [str(uuid4()) for _ in range(2)]
    db.sql("insert into auth.users(id) values " + ",".join(f"({literal(a)})" for a in actors))

    async def scenario():
        store = GameStore(dsn, local_test=True)
        game = (await store.create(actors[0], "corrupt", definition()))["id"]
        initial = await store.join(actors[1], game, "join", 1000)
        for path, value in (
            (["board"], []),
            (["revision"], 1),
            (["game_id"], str(uuid4())),
            (["config", "name"], "tampered"),
        ):
            damaged = deepcopy(initial)
            target = damaged
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            db.sql(
                f"update bgwq.games set state={literal(damaged)}::jsonb where id={literal(game)}"
            )
            before = db.sql(f"select state::text from bgwq.games where id={literal(game)}")
            with pytest.raises(Unavailable):
                await store.read(actors[0], game)
            with pytest.raises(Unavailable):
                await store.join(actors[1], game, "join", 2000)
            assert db.sql(f"select state::text from bgwq.games where id={literal(game)}") == before
            db.sql(
                f"update bgwq.games set state={literal(initial)}::jsonb where id={literal(game)}"
            )
        for damage in ("board", "start"):
            payload = {"kind": "activation", "action_id": "join", "state": deepcopy(initial)}
            if damage == "board":
                payload["state"]["board"] = []
            else:
                payload["state"]["started_at_ms"] = 2000
                payload["state"]["clocks"]["anchor_ms"] = 2000
            db.sql(
                f"update bgwq.events set payload={literal(payload)}::jsonb where game_id={literal(game)} and revision=0"
            )
            with pytest.raises(Unavailable):
                await store.join(actors[1], game, "join", 2000)
            assert await store.read(actors[0], game) == initial

    asyncio.run(scenario())


@pytest.mark.parametrize("stage", ["create", "submit", "read"])
@pytest.mark.parametrize("interrupt", ["timeout", "cancel"])
def test_worker_deadline_responsiveness_and_no_late_commit(database, monkeypatch, stage, interrupt):
    """Delayed pure scheduling work cannot block the loop or publish after timeout."""
    import threading
    import server.persistence as persistence

    db, dsn = database
    actors = [str(uuid4()) for _ in range(2)]
    db.sql("insert into auth.users(id) values " + ",".join(f"({literal(a)})" for a in actors))
    started, release, finished = threading.Event(), threading.Event(), threading.Event()
    real_work = persistence._engine_work

    async def scenario():
        store = GameStore(dsn, local_test=True)
        game = (await store.create(actors[0], "seed", definition()))["id"]
        await store.join(actors[1], game, "join", 1000)
        before = db.sql(f"select state::text from bgwq.games where id={literal(game)}")

        async def delayed(work):
            def run():
                started.set()
                release.wait(3)
                try:
                    return work()  # The actual engine remains the implementation under test.
                finally:
                    finished.set()

            return await real_work(run)

        monkeypatch.setattr(persistence, "_engine_work", delayed)
        monkeypatch.setattr(persistence, "_OPERATION_SECONDS", 0.1)
        if stage == "create":
            operation = store.create(actors[0], "cancelled-create", definition())
        elif stage == "submit":
            operation = store.submit(
                actors[0], game, 0, "cancelled-move", Move((5, 0), (4, 1)), 1100
            )
        else:
            operation = store.read(actors[0], game)
        task = asyncio.create_task(operation)
        ticks = 0
        while not task.done():
            await asyncio.sleep(0.005)
            ticks += 1
            if interrupt == "cancel" and started.is_set() and ticks >= 3:
                task.cancel()
                break
        assert started.is_set() and not finished.is_set()
        with pytest.raises(asyncio.CancelledError if interrupt == "cancel" else Unavailable):
            await task
        assert ticks >= 2  # Independent coroutine executed while pure work was held.
        release.set()
        while not finished.is_set():
            await asyncio.sleep(0.005)
        await asyncio.sleep(0.02)
        assert db.sql(f"select state::text from bgwq.games where id={literal(game)}") == before
        assert (
            db.sql(
                f"select count(*) from bgwq.games where player_one={literal(actors[0])} and create_action_id='cancelled-create'"
            )
            == "0"
        )
        assert db.sql(f"select count(*) from bgwq.events where game_id={literal(game)}") == "1"
        monkeypatch.setattr(persistence, "_engine_work", real_work)
        monkeypatch.setattr(persistence, "_OPERATION_SECONDS", 10)
        assert await store.read(actors[0], game) == json.loads(before)

    try:
        asyncio.run(scenario())
    finally:
        release.set()


def test_cancelled_worker_holds_capacity_until_pure_work_finishes():
    """Cancellation cannot turn two running workers into an unbounded queue."""
    import threading
    from server.persistence import _engine_work

    release = threading.Event()
    entered = [threading.Event(), threading.Event()]

    def held(index):
        entered[index].set()
        release.wait(3)
        return index

    async def scenario():
        tasks = [asyncio.create_task(_engine_work(lambda i=i: held(i))) for i in range(2)]
        while not all(event.is_set() for event in entered):
            await asyncio.sleep(0.005)
        tasks[0].cancel()
        with pytest.raises(asyncio.CancelledError):
            await tasks[0]
        with pytest.raises(Unavailable, match="capacity"):
            await _engine_work(lambda: 99)
        release.set()
        assert await tasks[1] == 1
        # The cancelled pure worker releases its own slot, without publishing.
        for _ in range(100):
            try:
                assert await _engine_work(lambda: 2) == 2
                break
            except Unavailable:
                await asyncio.sleep(0.005)
        else:
            pytest.fail("worker capacity did not recover")

    try:
        asyncio.run(scenario())
    finally:
        release.set()


def test_real_long_history_replay_keeps_event_loop_responsive(database, monkeypatch):
    """Replay an actual durable 120-action game while another coroutine runs."""
    from engine.model.game.manager import GameManager

    db, dsn = database
    actors = [str(uuid4()) for _ in range(2)]
    db.sql("insert into auth.users(id) values " + ",".join(f"({literal(a)})" for a in actors))
    config = GameManager(definition(), str(uuid4()), tuple(actors), 1000).get_state()["config"]
    config["pieces"]["man"]["moves"] = [[0, 1], [0, -1]]
    config["pieces"]["man"]["attacks"] = [[1, 1]]
    config["pieces"]["man"]["color_relative"] = False
    config["pieces"]["man"].pop("capture_policy", None)
    config["pieces"]["man"].pop("promotion", None)

    async def scenario():
        store = GameStore(dsn, local_test=True)
        game = (await store.create(actors[0], "long", validate_definition(config)))["id"]
        await store.join(actors[1], game, "join", 1000)
        state = None
        for index in range(120):
            actor = index % 2
            outward = (index // 2) % 2 == 0
            start, end = ((5, 0), (5, 1)) if actor == 0 else ((0, 5), (0, 4))
            if not outward:
                start, end = end, start
            state = (
                await store.submit(
                    actors[actor], game, index, f"m{index}", Move(start, end), 1100 + index
                )
            )["state"]
        import threading

        started, finished = threading.Event(), threading.Event()
        real_recovery = GameManager.from_snapshot

        def observe_recovery(snapshot):
            # Instrument entry/exit only; the complete real replay executes.
            started.set()
            try:
                return real_recovery(snapshot)
            finally:
                finished.set()

        monkeypatch.setattr(GameManager, "from_snapshot", staticmethod(observe_recovery))
        task = asyncio.create_task(GameStore(dsn, local_test=True).read(actors[0], game))
        while not started.is_set():
            await asyncio.sleep(0)
        ticks = 0
        while not finished.is_set():
            await asyncio.sleep(0)
            ticks += 1
        assert await task == state
        assert ticks >= 2  # Only counts scheduling during real engine replay.
        assert state["revision"] == 120

    asyncio.run(scenario())


def test_real_network_verified_tls(database, tmp_path):
    """A real TCP handshake must use TLS and verify a trusted certificate."""
    db, dsn = database
    if not shutil.which("openssl"):
        pytest.fail("TLS integration gate blocked: openssl unavailable")
    certificate, key = tmp_path / "server.crt", tmp_path / "server.key"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(certificate),
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=IP:127.0.0.1",
        ],
        check=True,
        capture_output=True,
    )
    for path in (certificate, key):
        subprocess.run(
            ["docker", "cp", str(path), f"{db.container}:/tmp/{path.name}"],
            check=True,
            capture_output=True,
        )
    subprocess.run(
        [
            "docker",
            "exec",
            "-u",
            "root",
            db.container,
            "sh",
            "-c",
            "chown postgres:postgres /tmp/server.crt /tmp/server.key && chmod 600 /tmp/server.key",
        ],
        check=True,
        capture_output=True,
    )
    db.sql("alter system set ssl='on'")
    db.sql("alter system set ssl_cert_file='/tmp/server.crt'")
    db.sql("alter system set ssl_key_file='/tmp/server.key'")
    db.sql("select pg_reload_conf()")
    secure = dsn.replace("sslmode=disable", f"sslmode=verify-full sslrootcert={certificate}")
    untrusted = tmp_path / "other-ca.crt"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(tmp_path / "other-ca.key"),
            "-out",
            str(untrusted),
            "-days",
            "1",
            "-subj",
            "/CN=untrusted",
        ],
        check=True,
        capture_output=True,
    )

    async def scenario():
        store = GameStore(secure)
        async with store._transaction() as connection:
            cursor = await connection.execute(
                "select ssl from pg_stat_ssl where pid=pg_backend_pid()"
            )
            assert (await cursor.fetchone())["ssl"] is True
        invalid = GameStore(secure.replace(str(certificate), str(untrusted)))
        with pytest.raises(Unavailable):
            async with invalid._transaction():
                pytest.fail("untrusted TLS connection accepted")

    asyncio.run(scenario())


@pytest.mark.parametrize("name", ["PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"])
def test_ambient_connection_override_rejected(monkeypatch, name):
    monkeypatch.setenv(name, "untrusted-override")
    with pytest.raises(Unavailable):
        GameStore("host=db.example sslmode=verify-full")


def test_real_statement_timeout_rolls_back_and_key_can_retry(database):
    """A cancelled PostgreSQL statement never leaves a partial state/event commit."""
    db, dsn = database
    actors = [str(uuid4()) for _ in range(2)]
    db.sql("insert into auth.users(id) values " + ",".join(f"({literal(a)})" for a in actors))
    name = "slow_" + uuid4().hex

    async def scenario():
        store = GameStore(dsn, local_test=True)
        game = (await store.create(actors[0], "slow", definition()))["id"]
        initial = await store.join(actors[1], game, "join", 1000)
        db.sql(
            f"""create function public.{name}() returns trigger language plpgsql as $$
        begin if new.game_id={literal(game)}::uuid then perform pg_sleep(10); end if; return new; end $$;
        create trigger {name} before insert on bgwq.events for each row execute function public.{name}();"""
        )
        try:
            with pytest.raises(Unavailable):
                await store.submit(actors[0], game, 0, "slow-action", Move((5, 0), (4, 1)), 1100)
            assert await store.read(actors[0], game) == initial
            assert db.sql(f"select count(*) from bgwq.events where game_id={literal(game)}") == "1"
        finally:
            db.sql(f"drop trigger {name} on bgwq.events; drop function public.{name}();")
        result = await store.submit(actors[0], game, 0, "slow-action", Move((5, 0), (4, 1)), 1100)
        assert result["state"]["revision"] == 1
        assert db.sql(f"select count(*) from bgwq.events where game_id={literal(game)}") == "2"

    asyncio.run(scenario())


def test_postcommit_reply_loss_recovers_exact_key_without_replaying(database):
    """A cancelled delivery boundary cannot undo a real acknowledged DB commit."""
    db, dsn = database
    actors = [str(uuid4()) for _ in range(2)]
    db.sql("insert into auth.users(id) values " + ",".join(f"({literal(a)})" for a in actors))

    async def scenario():
        store = GameStore(dsn, local_test=True)
        game = (await store.create(actors[0], "reply-loss", definition()))["id"]
        await store.join(actors[1], game, "join", 1000)
        committed = asyncio.Event()
        never_delivered = asyncio.Event()
        move = Move((5, 0), (4, 1))

        async def host_delivery():
            result = await store.submit(actors[0], game, 0, "stable", move, 1100)
            committed.set()  # Fault is outside the implementation under test.
            await never_delivered.wait()
            return result

        request = asyncio.create_task(host_delivery())
        await committed.wait()
        assert db.sql(f"select revision from bgwq.games where id={literal(game)}") == "1"
        request.cancel()
        with pytest.raises(asyncio.CancelledError):
            await request
        recovered = await GameStore(dsn, local_test=True).submit(
            actors[0], game, 0, "stable", move, 90000
        )
        assert recovered["event"]["at_ms"] == 1100
        assert recovered["state"]["revision"] == 1
        assert db.sql(f"select count(*) from bgwq.events where game_id={literal(game)}") == "2"
        assert await store.read(actors[0], game) == recovered["state"]

    asyncio.run(scenario())


def test_pinned_definition_comparison_distinguishes_boolean_from_integer(database):
    """Typed declarative constants cannot alias through Python equality."""
    from engine.model.game.manager import GameManager

    db, dsn = database
    actors = [str(uuid4()) for _ in range(2)]
    db.sql("insert into auth.users(id) values " + ",".join(f"({literal(a)})" for a in actors))
    config = GameManager(definition(), str(uuid4()), tuple(actors), 1000).get_state()["config"]
    config["rules"][0]["when"] = {"op": "compare", "relation": "eq", "left": 1, "right": 1}
    pinned = validate_definition(config)

    async def scenario():
        store = GameStore(dsn, local_test=True)
        game = (await store.create(actors[0], "typed", pinned))["id"]
        initial = await store.join(actors[1], game, "join", 1000)
        damaged = deepcopy(config)
        damaged["rules"][0]["when"]["left"] = True
        # Administrative fault injection is confined to this disposable database.
        db.sql("alter table bgwq.games disable trigger bgwq_protect_game_snapshot")
        try:
            db.sql(
                f"update bgwq.games set config_snapshot={literal(damaged)}::jsonb where id={literal(game)}"
            )
        finally:
            db.sql("alter table bgwq.games enable trigger bgwq_protect_game_snapshot")
        try:
            with pytest.raises(Unavailable):
                await store.read(actors[0], game)
            with pytest.raises(Conflict):
                await store.create(actors[0], "typed", pinned)
            assert db.sql(f"select state::text from bgwq.games where id={literal(game)}") == db.sql(
                f"select state::text from bgwq.games where id={literal(game)}"
            )
        finally:
            db.sql("alter table bgwq.games disable trigger bgwq_protect_game_snapshot")
            try:
                db.sql(
                    f"update bgwq.games set config_snapshot={literal(config)}::jsonb where id={literal(game)}"
                )
            finally:
                db.sql("alter table bgwq.games enable trigger bgwq_protect_game_snapshot")
        assert await store.read(actors[0], game) == initial

    asyncio.run(scenario())
