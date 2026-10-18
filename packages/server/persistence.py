"""Internal participant-scoped persistence with bounded pure engine workers.

Workers cannot access a connection. Cancelled work can finish computation but
cannot publish its output or commit a transaction. No authoritative cache exists.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import ipaddress
import json
import os
import re
from threading import BoundedSemaphore
from typing import Any, AsyncIterator, Awaitable, Callable, TypeVar
from uuid import UUID, uuid4

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from engine.model.game.configuration import GameDefinition, validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move

T = TypeVar("T")
_OPERATION_SECONDS = 10
_ENGINE_WORKERS = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bgwq-engine")
_ENGINE_SLOTS = BoundedSemaphore(2)


class StoreError(Exception):
    """Safe persistence failure without database diagnostics."""


class InvalidInput(StoreError):
    """Caller supplied malformed trusted arguments."""


class Denied(StoreError):
    """Game unavailable to this identity, including nonexistent games."""


class Conflict(StoreError):
    """Revision or idempotency key conflicts; never automatically replay."""


class Rejected(StoreError):
    """The authoritative engine rejected the transition."""


class Unavailable(StoreError):
    """Persistence configuration, data, capacity or service is unavailable."""


def _uuid(value: str) -> None:
    """Require a canonical UUID.

    Args:
        value: Identity supplied by the verified host.

    Raises:
        InvalidInput: The identity is not canonical.
    """
    try:
        if type(value) is not str or str(UUID(value)) != value:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise InvalidInput("canonical identity required") from None


def _action(value: str) -> None:
    """Require a bounded UTF-8 action identifier.

    Args:
        value: Stable request identifier.

    Raises:
        InvalidInput: The identifier cannot be persisted safely.
    """
    if type(value) is not str or not 1 <= len(value) <= 128 or "\x00" in value:
        raise InvalidInput("bounded action identifier required")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise InvalidInput("bounded action identifier required") from None


def _integer(value: int, maximum: int) -> None:
    """Require a strict nonnegative integer.

    Args:
        value: Untrusted scalar.
        maximum: Inclusive ceiling.

    Raises:
        InvalidInput: The scalar exceeds the contract.
    """
    if type(value) is not int or not 0 <= value <= maximum:
        raise InvalidInput("bounded integer required")


async def _engine_work(work: Callable[[], T]) -> T:
    """Run pure engine work without an unbounded queue or event-loop blocking.

    Args:
        work: A pure computation with no connection or publication capability.

    Returns:
        Computed value if its awaiting operation remains live.

    Raises:
        Unavailable: Both fixed worker slots are occupied.
    """
    if not _ENGINE_SLOTS.acquire(blocking=False):
        raise Unavailable("engine capacity unavailable")

    def run() -> T:
        try:
            return work()
        finally:
            _ENGINE_SLOTS.release()

    # Shield only the pure worker: cancellation of its waiter cannot cancel a
    # queued future before its finally releases the reserved capacity.
    future = asyncio.get_running_loop().run_in_executor(_ENGINE_WORKERS, run)
    future.add_done_callback(lambda done: done.exception() if not done.cancelled() else None)
    return await asyncio.shield(future)


def _recover(
    row: dict[str, Any], state: dict[str, Any] | None = None, *, genesis: bool = False
) -> GameManager:
    """Reconstruct pinned durable state and verify its containing row.

    Args:
        row: Participant-authorized database row with JSON text columns.
        state: Optional activation snapshot to validate against the same row.
        genesis: Require revision zero for activation recovery.

    Returns:
        Canonically reconstructed engine.

    Raises:
        Unavailable: Stored data or containing metadata is inconsistent.
    """
    try:
        snapshot = json.loads(row["state"]) if state is None else state
        config = json.loads(row["config_snapshot"])
        if (
            snapshot["game_id"] != str(row["id"])
            or snapshot["participants"]
            != {"1": str(row["player_one"]), "-1": str(row["player_two"])}
            or json.dumps(snapshot["config"], sort_keys=True) != json.dumps(config, sort_keys=True)
            or snapshot["revision"] != (0 if genesis else row["revision"])
            or (genesis and snapshot["started_at_ms"] != json.loads(row["state"])["started_at_ms"])
        ):
            raise ValueError
        return GameManager.from_snapshot(snapshot)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise Unavailable("persisted game unavailable") from None


class GameStore:
    """Private SQL adapter with a ten-second active-work deadline and cleanup tail.

    Args:
        dsn: Server-only DSN or BGWQ_DATABASE_DSN environment value.
        local_test: Allow disabled TLS only for an explicit loopback test DSN.

    Raises:
        Unavailable: A single explicit network host and verified TLS are absent.
    """

    def __init__(self, dsn: str | None = None, *, local_test: bool = False) -> None:
        """Validate an explicit single-host transport configuration.

        Args:
            dsn: Server-only DSN, or the dedicated environment variable.
            local_test: Allow disabled TLS on an explicit loopback endpoint.

        Raises:
            Unavailable: Transport identity or TLS configuration is unsafe.
        """
        try:
            selected = dsn if dsn is not None else os.environ["BGWQ_DATABASE_DSN"]
            options = conninfo_to_dict(selected)
            host = options.get("host", "")
            try:
                ipaddress.ip_address(host)
                network_host = True
            except ValueError:
                network_host = bool(
                    re.fullmatch(
                        r"(?=.{1,253}\.?$)[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.?", host
                    )
                )
            local = local_test is True and dsn is not None and host in {"127.0.0.1", "::1"}
            if (
                not network_host
                or options.get("hostaddr")
                or options.get("service")
                or options.get("options")
                or any(
                    os.environ.get(name) for name in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE")
                )
                or (
                    options.get("sslmode") != "verify-full"
                    and not (local and options.get("sslmode") == "disable")
                )
            ):
                raise ValueError
            self._dsn = selected
        except (KeyError, ValueError, TypeError, psycopg.Error):
            raise Unavailable("secure database configuration required") from None

    @asynccontextmanager
    async def _transaction(self) -> AsyncIterator[psycopg.AsyncConnection]:
        """Open one bounded transaction and redact database failures.

        Yields:
            Operation-local connection; cancellation rolls its transaction back.

        Raises:
            Denied: SQL authorization fails.
            Conflict: SQL revision, lifecycle or key conflicts.
            Unavailable: The database or durable data is unavailable.
        """
        try:
            connection = await psycopg.AsyncConnection.connect(
                self._dsn,
                connect_timeout=3,
                prepare_threshold=None,
                gssencmode="disable",
                row_factory=dict_row,
                options="-c statement_timeout=3000 -c lock_timeout=3000",
            )
            try:
                yield connection
                await connection.commit()
            except BaseException:
                # Cleanup has a separate three-second allowance. A detached
                # rollback can only roll back; it cannot publish a transition.
                rollback = asyncio.create_task(connection.rollback())
                rollback.add_done_callback(
                    lambda done: done.exception() if not done.cancelled() else None
                )
                completed, _ = await asyncio.wait({rollback}, timeout=3)
                if not completed:
                    connection.pgconn.finish()
                    rollback.cancel()
                raise
            finally:
                await connection.close()
        except psycopg.Error as error:
            if error.sqlstate == "42501":
                raise Denied("game unavailable") from None
            if error.sqlstate in {"23505", "40001", "40P01", "55000"}:
                raise Conflict("game request conflicts") from None
            raise Unavailable("database operation unavailable") from None
        except (ValueError, KeyError, TypeError, RecursionError):
            raise Unavailable("persisted game unavailable") from None

    async def _bounded(self, operation: Awaitable[T]) -> T:
        """Cancel active work after ten seconds, then drain bounded cleanup.

        Args:
            operation: Complete operation including canonicalization.

        Returns:
            Completed result, including an exact retry after ambiguous delivery.

        Raises:
            Unavailable: Active work expires; cancellation and rollback cleanup
                may extend response time. An unknown commit acknowledgement
                requires authoritative recovery with the same request key.
        """
        try:
            return await asyncio.wait_for(operation, timeout=_OPERATION_SECONDS)
        except asyncio.TimeoutError:
            raise Unavailable("database deadline exceeded") from None

    async def create(
        self, actor_id: str, action_id: str, definition: GameDefinition
    ) -> dict[str, Any]:
        """Recover a creator key or atomically create a pinned pending game.

        Args:
            actor_id: Verified creator UUID.
            action_id: Stable creation key.
            definition: Validated immutable definition.

        Returns:
            Participant-scoped pending summary.

        Raises:
            InvalidInput: Inputs are malformed.
            Conflict: The key has a different definition.
            Unavailable: Storage, capacity or the deadline fails.
        """
        _uuid(actor_id)
        _action(action_id)
        if not isinstance(definition, GameDefinition):
            raise InvalidInput("validated definition required")

        def canonicalize() -> tuple[dict[str, Any], str]:
            try:
                other = str(UUID(int=1 if actor_id != str(UUID(int=1)) else 2))
                config = GameManager(
                    definition, str(UUID(int=0)), (actor_id, other), 0
                ).get_state()["config"]
                return config, json.dumps(config)
            except ValueError:
                raise InvalidInput("invalid definition") from None

        async def operation() -> dict[str, Any]:
            config, encoded = await _engine_work(canonicalize)
            async with self._transaction() as db:
                await db.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (actor_id,)
                )
                cursor = await db.execute(
                    "SELECT id, config_snapshot::text FROM bgwq.games WHERE player_one=%s AND create_action_id=%s",
                    (actor_id, action_id),
                )
                row = await cursor.fetchone()
                if row and await _engine_work(
                    lambda: json.dumps(json.loads(row["config_snapshot"]), sort_keys=True)
                    != json.dumps(config, sort_keys=True)
                ):
                    raise Conflict("creation key conflicts")
                game_id = str(row["id"]) if row else str(uuid4())
                await db.execute(
                    "SELECT bgwq.create_game(%s,%s,%s,%s::jsonb)",
                    (game_id, actor_id, action_id, encoded),
                )
                return {"id": game_id, "lifecycle": "pending", "revision": 0, "creator": actor_id}

        return await self._bounded(operation())

    async def _load(
        self, db: psycopg.AsyncConnection, actor_id: str, game_id: str, *, joining: bool = False
    ) -> dict[str, Any]:
        """Load a row and enforce membership before any state is returned.

        Args:
            db: Operation connection.
            actor_id: Verified requesting identity.
            game_id: Canonical game UUID.
            joining: Defer membership to the activation boundary.

        Returns:
            Row with JSON text for decoding by a pure worker.

        Raises:
            Denied: The row is absent or private to another identity.
        """
        cursor = await db.execute(
            "SELECT id, player_one, player_two, lifecycle, revision, config_snapshot::text, state::text FROM bgwq.games WHERE id=%s",
            (game_id,),
        )
        row = await cursor.fetchone()
        if not row or (
            not joining and actor_id not in (str(row["player_one"]), str(row["player_two"]))
        ):
            raise Denied("game unavailable")
        return row

    async def join(
        self, actor_id: str, game_id: str, action_id: str, now_ms: int
    ) -> dict[str, Any]:
        """Activate once or recover a validated persisted genesis.

        Args:
            actor_id: Verified joining identity.
            game_id: Canonical game UUID.
            action_id: Stable activation key.
            now_ms: Trusted epoch milliseconds.

        Returns:
            Canonical genesis snapshot, including its persisted start time.

        Raises:
            InvalidInput: Inputs are malformed.
            Denied: Identity cannot join or recover this game.
            Conflict: Activation key or lifecycle conflicts.
            Unavailable: Durable state, capacity, database or deadline fails.
        """
        _uuid(actor_id)
        _uuid(game_id)
        _action(action_id)
        _integer(now_ms, 2**53 - 1)

        async def operation() -> dict[str, Any]:
            async with self._transaction() as db:
                await db.execute("SELECT id FROM bgwq.games WHERE id=%s FOR UPDATE", (game_id,))
                row = await self._load(db, actor_id, game_id, joining=True)
                if actor_id == str(row["player_one"]):
                    raise Denied("game unavailable")
                if row["lifecycle"] == "active":
                    if actor_id != str(row["player_two"]):
                        raise Denied("game unavailable")
                    cursor = await db.execute(
                        "SELECT payload::text FROM bgwq.events WHERE game_id=%s AND actor=%s AND action_scope='activation' AND action_id=%s",
                        (game_id, actor_id, action_id),
                    )
                    event = await cursor.fetchone()
                    if not event:
                        raise Conflict("activation key conflicts")

                    def recover() -> dict[str, Any]:
                        _recover(row)
                        payload = json.loads(event["payload"])
                        if (
                            set(payload) != {"kind", "action_id", "state"}
                            or payload["kind"] != "activation"
                            or payload["action_id"] != action_id
                        ):
                            raise Unavailable("persisted game unavailable")
                        return _recover(row, payload["state"], genesis=True).get_state()

                    return await _engine_work(recover)

                def genesis() -> tuple[dict[str, Any], str]:
                    state = GameManager(
                        validate_definition(json.loads(row["config_snapshot"])),
                        game_id,
                        (str(row["player_one"]), actor_id),
                        now_ms,
                    ).get_state()
                    return state, json.dumps(state)

                state, encoded = await _engine_work(genesis)
                await db.execute(
                    "SELECT bgwq.activate_game(%s,%s,%s,%s::jsonb)",
                    (game_id, actor_id, action_id, encoded),
                )
                return state

        return await self._bounded(operation())

    async def read(self, actor_id: str, game_id: str) -> dict[str, Any]:
        """Read participant-scoped metadata or canonically recovered state.

        Args:
            actor_id: Verified requesting identity.
            game_id: Canonical game UUID.

        Returns:
            Pending summary or validated active snapshot.

        Raises:
            InvalidInput: Identity is malformed.
            Denied: The game is unavailable to the identity.
            Unavailable: Durable state, capacity, database or deadline fails.
        """
        _uuid(actor_id)
        _uuid(game_id)

        async def operation() -> dict[str, Any]:
            async with self._transaction() as db:
                row = await self._load(db, actor_id, game_id)
                if row["lifecycle"] == "pending":
                    return {
                        "id": game_id,
                        "lifecycle": "pending",
                        "revision": 0,
                        "creator": str(row["player_one"]),
                    }
                return await _engine_work(lambda: _recover(row).get_state())

        return await self._bounded(operation())

    async def submit(
        self,
        actor_id: str,
        game_id: str,
        expected_revision: int,
        action_id: str,
        move: Move,
        now_ms: int,
    ) -> dict[str, Any]:
        """Authorize one move against recovered state, then CAS exactly once.

        Args:
            actor_id: Verified submitting identity.
            game_id: Canonical game UUID.
            expected_revision: Observed revision.
            action_id: Stable domain request key.
            move: Immutable canonical intent.
            now_ms: Trusted epoch milliseconds.

        Returns:
            Accepted event and authoritative state, including historical retries.

        Raises:
            InvalidInput: Inputs are malformed.
            Denied: Identity cannot access this game.
            Conflict: Revision, key or lifecycle conflicts.
            Rejected: Engine denies the move.
            Unavailable: Durable state, capacity, database or deadline fails.
        """
        _uuid(actor_id)
        _uuid(game_id)
        _action(action_id)
        _integer(expected_revision, 4095)
        _integer(now_ms, 2**53 - 1)
        if not isinstance(move, Move):
            raise InvalidInput("move intent required")

        async def operation() -> dict[str, Any]:
            async with self._transaction() as db:
                row = await self._load(db, actor_id, game_id)
                if row["lifecycle"] != "active":
                    raise Conflict("game is pending")

                def transition() -> tuple[dict[str, Any], dict[str, Any], str, str]:
                    manager = _recover(row)
                    observed = manager.get_state()
                    prior = next(
                        (e for e in observed["events"] if e["action_id"] == action_id), None
                    )
                    if prior:
                        if (
                            prior["actor"] != actor_id
                            or prior["expected_revision"] != expected_revision
                            or prior["move"] != move.to_json()
                        ):
                            raise Conflict("action key conflicts")
                    elif expected_revision != row["revision"]:
                        raise Conflict("stale game revision")
                    try:
                        event = manager.submit(actor_id, expected_revision, action_id, move, now_ms)
                    except TransitionError:
                        raise Rejected("transition rejected") from None
                    state = manager.get_state()
                    return event, state, json.dumps(state), json.dumps(event)

                event, state, encoded_state, encoded_event = await _engine_work(transition)
                if event["revision"] > row["revision"]:
                    await db.execute(
                        "SELECT bgwq.commit_revision(%s,%s,%s,%s::jsonb,%s::jsonb)",
                        (game_id, actor_id, row["revision"], encoded_state, encoded_event),
                    )
                return {"event": event, "state": state}

        return await self._bounded(operation())


def main() -> int:
    """Read a real provider game with a live verified identity; never write fixtures.

    Missing inputs exit two, unsuccessful verification exits one. This read-only
    probe does not certify hosted mutation, HTTP or Realtime acceptance.

    Returns:
        Zero for verification success, one for failure, two for missing inputs.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-provider", action="store_true", required=True)
    parser.parse_args()
    required = (
        "BGWQ_DATABASE_DSN",
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "BGWQ_REGISTERED_ACCESS_TOKEN",
        "BGWQ_REGISTERED_USER_ID",
        "BGWQ_PROVIDER_GAME_ID",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("Persistence provider gate blocked: missing " + ", ".join(missing), file=sys.stderr)
        return 2

    async def verify() -> None:
        from server.auth import SupabaseAuth

        identity = await SupabaseAuth.from_environment().authenticate(
            os.environ["BGWQ_REGISTERED_ACCESS_TOKEN"]
        )
        if identity.id != os.environ["BGWQ_REGISTERED_USER_ID"]:
            raise Denied("identity mismatch")
        await GameStore().read(identity.id, os.environ["BGWQ_PROVIDER_GAME_ID"])

    try:
        asyncio.run(verify())
    except Exception:
        print("Persistence provider verification failed", file=sys.stderr)
        return 1
    print("Provider identity and participant-scoped database read passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
