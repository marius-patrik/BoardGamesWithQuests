"""Authoritative, replayable JSON game transitions with isolated effect execution.

Every accepted intent produces one revision and one durable event. Identity,
turn, candidate legality and every configured effect are checked before publishing
new state. Persistence adapters must additionally enforce database compare-and-swap.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import asdict
from contextlib import contextmanager
import json
from threading import RLock
from typing import Any

from model.game.board import Board
from model.game.board_queries import BoardQueries
from model.game.capture_geometry import CaptureEnumerator
from model.game.capture_policy import (
    CapturePolicy,
    EvaluationBudget,
    MAX_EVALUATION_WORK,
)
from model.game.conditions import ConditionEvaluator, QueryResolutionError
from model.game.definition import (
    MAX_GAME_JSON_BYTES,
    GameDefinition,
    board_from_definition,
    validate_definition,
)
from model.game.hooks import HookInterpreter, PlannedEffect, RuleProgram
from model.game.move import Move
from model.game.outcomes import resolve_outcome
from model.game.schema import freeze_json, thaw_json, _json_work
from model.game.snapshot_queries import SnapshotQueries
from model.game.validator import MoveValidator
from model.pieces.piece import Piece

MAX_EVENTS = 4096
MAX_SNAPSHOT_BYTES = 4194304
# Immutable snapshots have at most 65,536 value nodes; mapping keys add at most
# one traversal unit per value, and serialized text bounds its 64-character work.
MAX_REPLAY_INITIAL_WORK = 2 * 65536 + MAX_SNAPSHOT_BYTES // 64
MAX_REPLAY_WORK = MAX_EVENTS * MAX_EVALUATION_WORK + MAX_REPLAY_INITIAL_WORK


class OperationEvaluation:
    """Own one aggregate work budget and exact-position capture cache.

    Args:
        budget: Trusted ceiling shared by every phase of one locked operation.
    """

    def __init__(self, budget: EvaluationBudget) -> None:
        """Initialize operation-local bounded capture storage.

        Args:
            budget: Shared deterministic work counter.
        """
        self.budget = budget
        self.capture_cache: dict[tuple[Any, ...], tuple[Any, ...]] = {}
        self.identity_cache: dict[str, str] = {}
        self.identity_probe_depth = 0


class TransitionError(ValueError):
    """An action is rejected without changing any authoritative session state."""


class GameManager:
    """Own one explicit configuration, two participants and revisioned game state.

    The manager is the sole domain transition boundary. A read or rejected action
    cannot consume clock time, mutate quests, append history or change the board.
    Session snapshots are detached JSON and reconstruct through deterministic replay.
    """

    def __init__(
        self,
        definition: GameDefinition,
        game_id: str,
        participant_ids: tuple[str, str],
        started_at_ms: int,
    ) -> None:
        """Create a session from explicit validated data and trusted server time.

        Args:
            definition: Validated data containing an explicit permits_move rule.
            game_id: Stable host-assigned identifier.
            participant_ids: Distinct identities for sides 1 and -1, in that order.
            started_at_ms: Nonnegative authoritative epoch milliseconds.

        Raises:
            TransitionError: Identities, timestamp or rule authority are invalid.
        """
        self._identifier(game_id)
        if (
            not isinstance(participant_ids, tuple)
            or len(participant_ids) != 2
            or participant_ids[0] == participant_ids[1]
        ):
            raise TransitionError("exactly two distinct participant identities are required")
        for identity in participant_ids:
            self._identifier(identity)
        self._timestamp(started_at_ms)
        if not isinstance(definition, GameDefinition) or not any(
            rule["hook"] == "permits_move" for rule in definition.rules
        ):
            raise TransitionError("a session requires explicit move authorization rules")
        self._definition = definition
        self._lock = RLock()
        self._evaluation: OperationEvaluation | None = None
        self._program = RuleProgram(definition.rules)
        config = {
            "schema_version": 2,
            "name": definition.name,
            "title": definition.title,
            "default": definition.default,
            "playable": definition.playable,
            "board": thaw_json(definition.board),
            "pieces": thaw_json(definition.pieces),
            "clock": thaw_json(definition.clock),
            "exports": list(definition.exports),
            "appearance": thaw_json(definition.appearance),
            "rules": thaw_json(definition.rules),
            "quests": thaw_json(definition.quests),
        }
        if "initial_state" in definition.declared_optional_fields or any(
            definition.initial_state.values()
        ):
            config["initial_state"] = thaw_json(definition.initial_state)
        if (
            "halfmove_reset" in definition.declared_optional_fields
            or definition.halfmove_reset is not None
        ):
            config["halfmove_reset"] = thaw_json(definition.halfmove_reset)
        if (
            "position_identity" in definition.declared_optional_fields
            or definition.position_identity is not None
        ):
            config["position_identity"] = thaw_json(definition.position_identity)
        if "starting_side" in definition.declared_optional_fields or definition.starting_side != 1:
            config["starting_side"] = definition.starting_side
        initial = definition.clock["initial_seconds"] * 1000
        self._config = freeze_json(config)
        state: dict[str, Any] = {
            "version": 1,
            "game_id": game_id,
            "config": config,
            "participants": {"1": participant_ids[0], "-1": participant_ids[1]},
            "started_at_ms": started_at_ms,
            "active_side": definition.starting_side,
            "board": self._placement(board_from_definition(definition)),
            "captured": [],
            "rule_state": thaw_json(definition.initial_state["rule_state"]),
            "special_rights": thaw_json(definition.initial_state["special_rights"]),
            "temporary_targets": thaw_json(definition.initial_state["temporary_targets"]),
            "clocks": {
                "remaining_ms": {"1": initial, "-1": initial},
                "anchor_ms": started_at_ms,
                "increment_ms": definition.clock["increment_seconds"] * 1000,
            },
            "quest_progress": {
                identity: {
                    quest["id"]: {"active": 0, "target": 1, "completed": False}
                    for quest in definition.quests
                }
                for identity in participant_ids
            },
            "outcome": None,
            "revision": 0,
            "halfmove_count": 0,
            "events": [],
            "position_history": [],
        }
        state["position_history"].append(self._position_key(state))
        self._state = freeze_json(state)

    @contextmanager
    def _operation(self, budget: EvaluationBudget | None = None) -> Iterator[None]:
        """Scope resources for one action, including an enclosing child replay counter.

        Args:
            budget: Optional explicit trusted counter for replay or verification.

        Yields:
            None while operation-local resources are active.
        """
        previous = self._evaluation
        if previous is None:
            self._evaluation = OperationEvaluation(
                budget if budget is not None else EvaluationBudget(MAX_EVALUATION_WORK)
            )
        try:
            yield
        finally:
            self._evaluation = previous

    def _copy_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        """Isolate mutable session facts while sharing the pinned immutable config.

        Args:
            state: Owned authoritative or candidate state.

        Returns:
            Independent mutable fields with a read-only configuration reference.
        """
        mutable = {
            key: value
            for key, value in state.items()
            if key not in {"config", "events", "position_history"}
        }
        self._charge(_json_work(mutable) + len(state["events"]) + len(state["position_history"]))
        copied = thaw_json(mutable)
        copied["config"] = self._config
        # Executors append entries; existing event records and position strings
        # are never mutated. Each projection owns both appendable containers.
        copied["events"] = list(state["events"])
        copied["position_history"] = list(state["position_history"])
        return copied

    def _charge(self, units: int = 1) -> None:
        """Reserve aggregate work before an operation phase executes.

        Args:
            units: Deterministic nonnegative work estimate.

        Raises:
            QueryResolutionError: Trusted aggregate operation budget is exhausted.
        """
        if self._evaluation is not None:
            self._evaluation.budget.consume(units)

    @property
    def definition(self) -> GameDefinition:
        """Read the immutable configuration pinned when the session was created.

        Returns:
            The validated immutable session definition.
        """
        return self._definition

    @staticmethod
    def _identifier(value: Any) -> None:
        """Check a bounded stable identity rather than coercing anonymous values.

        Args:
            value: Identifier supplied by a trusted host or authenticated caller.

        Raises:
            TransitionError: Identifier is empty, nontext or excessively long.
        """
        if not isinstance(value, str) or not 1 <= len(value) <= 128:
            raise TransitionError("identifiers must be nonempty bounded strings")

    @staticmethod
    def _timestamp(value: Any) -> None:
        """Reject noninteger, negative and unbounded authoritative timestamps.

        Args:
            value: Server epoch milliseconds.

        Raises:
            TransitionError: The supplied timestamp is invalid.
        """
        if type(value) is not int or not 0 <= value <= 2**53 - 1:
            raise TransitionError("timestamp must be nonnegative integer milliseconds")

    def _placement(self, board: Board) -> list[dict[str, Any]]:
        """Serialize pieces in stable row-major order, including movement rights.

        Args:
            board: Isolated board storage.

        Returns:
            Detached JSON piece records.
        """
        self._charge(board.rows * board.cols)
        return [
            {
                "square": [row, col],
                "kind": board.get_piece_at((row, col)).getType(),
                "side": board.get_piece_at((row, col)).getColor(),
                "moved": board.get_piece_at((row, col)).hasMoved(),
            }
            for row in range(board.rows)
            for col in range(board.cols)
            if board.get_piece_at((row, col)) is not None
        ]

    def _piece(self, kind: str, side: int, moved: bool = False) -> Piece:
        """Build a piece from configuration capabilities without type-name branches.

        Args:
            kind: Configured piece key.
            side: Explicit side 1 or -1.
            moved: Persisted movement-right flag.

        Returns:
            A new isolated piece.

        Raises:
            TransitionError: The piece kind is unavailable.
        """
        if kind not in self.definition.pieces:
            raise TransitionError("unknown configured piece kind")
        spec = self.definition.pieces[kind]

        def vectors(field: str) -> list[tuple[int, int]]:
            """Resolve color-relative vectors from the selected piece data.

            Args:
                field: A movement vector field.

            Returns:
                Detached side-specific integer vector pairs.
            """
            return [
                (row * side if spec.get("color_relative") else row, col)
                for row, col in spec.get(field, ())
            ]

        piece = Piece(
            color=side,
            piece_type=kind,
            vectors=vectors("moves"),
            attack_vectors=vectors("attacks"),
            can_jump=spec["jump"],
            name=kind,
            max_steps=None if spec["repeat"] else 1,
            initial_vectors=vectors("initial_moves"),
            symbols=(spec["symbols"]["white"], spec["symbols"]["black"]),
        )
        piece.setMoved(moved)
        return piece

    def _board(self, state: Mapping[str, Any]) -> Board:
        """Rebuild board storage from an isolated authoritative position.

        Args:
            state: Detached validated session data.

        Returns:
            A board with independent piece instances.
        """
        self._charge(
            self.definition.board["rows"] * self.definition.board["columns"] + len(state["board"])
        )
        return Board(
            (self.definition.board["rows"], self.definition.board["columns"]),
            placement=[
                (
                    tuple(record["square"]),
                    self._piece(record["kind"], record["side"], record["moved"]),
                )
                for record in state["board"]
            ],
        )

    @staticmethod
    def _raw_position_key(state: Mapping[str, Any]) -> str:
        """Canonicalize rule-significant board and explicit rights for repetition.

        Args:
            state: Detached session data.

        Returns:
            Stable JSON position key.
        """
        return json.dumps(
            {
                "board": state["board"],
                "active_side": state["active_side"],
                "rights": state["special_rights"],
                "targets": state["temporary_targets"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def _position_key(self, state: Mapping[str, Any]) -> str:
        """Normalize only configured rule-significant state and legally effective targets.

        Args:
            state: Detached authoritative or isolated prospective state.

        Returns:
            Canonical position identity, preserving raw identity when policy is absent.

        Raises:
            QueryResolutionError: Selected state, legality probes or resources are invalid.
        """
        policy = self.definition.position_identity
        if policy is None:
            return self._raw_position_key(state)
        if self._evaluation is None:
            with self._lock, self._operation():
                return self._position_key(state)
        if self._evaluation.identity_probe_depth:
            raise QueryResolutionError("recursive position identity is not available")
        identity_input = {key: value for key, value in state.items() if key != "config"}
        self._charge(_json_work(identity_input))
        cache_key = json.dumps(thaw_json(identity_input), sort_keys=True, separators=(",", ":"))
        if cache_key in self._evaluation.identity_cache:
            return self._evaluation.identity_cache[cache_key]
        targets: dict[str, Any] = {}
        for target in policy["targets"]:
            name = target["name"]
            value = state["temporary_targets"][name]
            if value is not None and target["legal_capture"]:
                self._evaluation.identity_probe_depth += 1
                try:
                    value = (
                        value
                        if self._legal_target_capture(self._copy_state(state), value)
                        else None
                    )
                finally:
                    self._evaluation.identity_probe_depth -= 1
            targets[name] = value
        position = {
            "board": [
                {
                    key: value
                    for key, value in record.items()
                    if key != "moved" or record["kind"] in policy["moved_kinds"]
                }
                for record in state["board"]
            ],
            "active_side": state["active_side"],
            "rule_state": {name: state["rule_state"][name] for name in policy["rule_state"]},
            "rights": {name: state["special_rights"][name] for name in policy["rights"]},
            "targets": targets,
        }
        result = json.dumps(thaw_json(position), sort_keys=True, separators=(",", ":"))
        if len(self._evaluation.identity_cache) >= 256:
            self._evaluation.identity_cache.pop(next(iter(self._evaluation.identity_cache)))
        self._evaluation.identity_cache[cache_key] = result
        return result

    def _legal_target_capture(self, state: dict[str, Any], target: list[int]) -> bool:
        """Probe full configured capture legality without appending recursive position history.

        Args:
            state: Isolated observed position.
            target: In-bounds temporary target.

        Returns:
            Whether a complete authorized capturing intent ends on the target.

        Raises:
            QueryResolutionError: Probe requests recursive identity or exceeds resources.
        """
        side = state["active_side"]
        board = self._board(state)
        offered_intents = self._offers(state, board, side, state["clocks"]["anchor_ms"])
        for move in self._candidates(
            state, board, side, state["clocks"]["anchor_ms"], offered_intents
        ):
            if move.end_pos != tuple(target):
                continue
            try:
                _, _, captures, _, _ = self._prepare_move(
                    state,
                    side,
                    state["participants"][str(side)],
                    state["revision"],
                    "position-probe",
                    move,
                    state["clocks"]["anchor_ms"],
                    enforce_clock=False,
                    offered_intents=offered_intents,
                    preview=True,
                )
            except TransitionError:
                continue
            if captures:
                return True
        return False

    def _paths(self, board: Board, side: int) -> list[dict[str, Any]]:
        """Enumerate complete capture chains only for pieces declaring that policy.

        Args:
            board: Position under evaluation.
            side: Participant side.

        Returns:
            Complete ordered routes from configured capture policies.

        Raises:
            QueryResolutionError: Enumeration exceeds bounded search resources.
        """
        placement = self._placement(board)
        key = (
            board.rows,
            board.cols,
            side,
            tuple(
                (tuple(record["square"]), record["kind"], record["side"], record["moved"])
                for record in placement
            ),
        )
        if self._evaluation is not None and key in self._evaluation.capture_cache:
            cached = self._evaluation.capture_cache[key]
            self._charge(_json_work(cached))
            return thaw_json(cached)
        routes: list[dict[str, Any]] = []
        budget = self._evaluation.budget if self._evaluation is not None else None
        enumerator = CaptureEnumerator(board, budget)
        for record in placement:
            self._charge()
            if record["side"] != side:
                continue
            spec = self.definition.pieces[record["kind"]]
            if "capture_policy" in spec:
                routes.extend(
                    enumerator.enumerate(
                        tuple(record["square"]),
                        CapturePolicy.from_json(spec["capture_policy"]),
                        (
                            (0 if side == 1 else board.rows - 1)
                            if spec.get("promotion", {}).get("stop_capture")
                            else None
                        ),
                    )
                )
            if len(routes) > 128:
                raise QueryResolutionError("capture path result exceeds bounded resources")
        if self._evaluation is not None:
            if len(self._evaluation.capture_cache) >= 256:
                self._evaluation.capture_cache.pop(next(iter(self._evaluation.capture_cache)))
            self._charge(_json_work(routes))
            self._evaluation.capture_cache[key] = freeze_json(routes)
        return routes

    def _context(
        self,
        state: dict[str, Any],
        board: Board,
        side: int,
        move: Move | None,
        captures: list[list[int]],
        now_ms: int,
        counts: dict[str, int] | None = None,
        before_board: Board | None = None,
        projected_board: Board | None = None,
        action: dict[str, Any] | None = None,
        expired_side: int | None = None,
        event_actor: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Bind read-only queries and references to one explicit evaluation state.

        Args:
            state: Isolated session state.
            board: Board corresponding to that state.
            side: Evaluation participant side.
            move: Candidate intent, or None for state queries.
            captures: Server-derived captured coordinates.
            now_ms: Trusted timestamp for derived remaining time.
            counts: Computed legal counts, or None when unavailable.
            before_board: Original board for explicit before-phase queries.
            projected_board: Fully isolated projection for after-phase safety queries.

        Returns:
            Trusted query registry and detached reference bindings.
        """
        selectors = {"active": side, "opponent": -side}
        query_state = {
            "rule_state": state["rule_state"],
            "special_rights": state["special_rights"],
            "temporary_targets": state["temporary_targets"],
            "move_attributes": {
                "captures": len(captures),
                "start": list(move.start_pos) if move else None,
                "end": list(move.end_pos) if move else None,
                "promotion": move.promotion if move else None,
            },
            "capture_paths": {name: self._paths(board, color) for name, color in selectors.items()},
            "promotion_options": None,
            "clocks": {
                name: max(
                    0,
                    state["clocks"]["remaining_ms"][str(color)]
                    - (
                        now_ms - state["clocks"]["anchor_ms"]
                        if color == state["active_side"]
                        else 0
                    ),
                )
                // 1000
                for name, color in selectors.items()
            },
            "position_key": None,
            "position_history": state["position_history"],
            "position": {"board": state["board"], "active_side": state["active_side"]},
            "halfmove_count": state["halfmove_count"],
            "last_action": state["events"][-1] if state["events"] else None,
            "participants": {
                name: {"id": state["participants"][str(color)], "side": color}
                for name, color in selectors.items()
            },
            "quest_progress": {
                name: state["quest_progress"][state["participants"][str(color)]]
                for name, color in selectors.items()
            },
            "events": state["events"],
        }
        if counts is not None:
            query_state["legal_move_counts"] = counts
        references = {
            "player.id": state["participants"][str(side)],
            "player.side": side,
            "game.revision": state["revision"],
            "board.rows": board.rows,
            "board.columns": board.cols,
            "clock.remaining": query_state["clocks"]["active"],
            "player.opponent.id": state["participants"][str(-side)],
            "event.type": (
                action["type"] if action is not None else ("move" if move is not None else None)
            ),
            "event.claim": action.get("claim") if action is not None else None,
            "event.actor": event_actor or state["participants"][str(side)],
            "event.expired_side": expired_side,
        }
        if move is not None:
            references.update(
                {
                    "move.start": list(move.start_pos),
                    "move.end": list(move.end_pos),
                    "move.hops": [list(square) for square in move.hops],
                    "move.promotion": move.promotion,
                    "move.captures": len(captures),
                }
            )
        snapshot_fields = {
            "rule_state": "rule_state",
            "special_rights": "special_rights",
            "temporary_target": "temporary_targets",
            "move_attribute": "move_attributes",
            "capture_count": "capture_paths",
            "capture_paths": "capture_paths",
            "promotion_options": "promotion_options",
            "clock_remaining": "clocks",
            "history_count": "events",
            "halfmove_count": "halfmove_count",
            "last_action": "last_action",
            "legal_move_count": "legal_move_counts",
            "participant": "participants",
            "position": "position",
            "quest_progress": "quest_progress",
            "repetition_count": "position_history",
        }
        field_work: dict[str, int] = {}
        snapshots: dict[str, SnapshotQueries] = {}

        def snapshot_query(name: str) -> Any:
            """Bind only the field read by one snapshot operation.

            Args:
                name: Whitelisted snapshot query name.

            Returns:
                A query closure owning detached field data on its first use.
            """

            def invoke(params: Mapping[str, Any]) -> Any:
                """Read a detached field from one isolated evaluation context.

                Args:
                    params: Closed declarative query parameters.

                Returns:
                    A detached query result.
                """
                field = snapshot_fields[name]
                if name == "capture_count" and params.get("scope") == "candidate":
                    field = "move_attributes"
                if field == "promotion_options" and query_state[field] is None:
                    records = self._placement(before_board or board)
                    query_state[field] = {
                        selector: sorted(
                            {
                                option
                                for record in records
                                if record["side"] == color
                                for option in self.definition.pieces[record["kind"]]
                                .get("promotion", {})
                                .get("options", ())
                            }
                        )
                        for selector, color in selectors.items()
                    }
                if field not in query_state:
                    raise QueryResolutionError(f"snapshot field is unavailable: {field}")
                if field not in snapshots:
                    field_work[field] = _json_work(query_state[field])
                    self._charge(2 * field_work[field])
                    snapshots[field] = SnapshotQueries({field: thaw_json(query_state[field])})
                self._charge(field_work[field])
                return snapshots[field].bindings()[name](params)

            return invoke

        self._charge(len(query_state) + len(references))
        budget = self._evaluation.budget if self._evaluation is not None else None
        queries = {
            **BoardQueries(board, side, budget).bindings(),
            **{
                name: snapshot_query(name) for name in snapshot_fields if name != "repetition_count"
            },
            "turn": BoardQueries(board, state["active_side"], budget).turn,
        }

        def repetition(params: Mapping[str, Any]) -> int:
            """Resolve position normalization only when repetition is queried.

            Args:
                params: Validated repetition query parameters.

            Returns:
                Occurrences of the effective position in the bound history.
            """
            key = (
                None
                if self._evaluation is not None and self._evaluation.identity_probe_depth
                else self._position_key(state)
            )
            self._charge(3 * _json_work(state["position_history"]) + _json_work(key))
            return SnapshotQueries(
                {"position_key": key, "position_history": state["position_history"]}
            ).repetition_count(params)

        queries["repetition_count"] = repetition
        for name in BoardQueries(board, side, budget).bindings():
            if name == "turn":
                continue
            ordinary = queries[name]

            def phased(
                params: Mapping[str, Any], name: str = name, ordinary: Any = ordinary
            ) -> Any:
                """Read an explicit board phase without speculative recursive evaluation.

                Args:
                    params: Validated query parameters with optional phase.
                    name: Bound board-query operation.
                    ordinary: Default lifecycle query implementation.

                Returns:
                    Isolated JSON board facts.

                Raises:
                    QueryResolutionError: Phase is unknown or projection is unavailable.
                """
                values = dict(params)
                phase = values.pop("phase", None)
                if phase is None:
                    if name == "pieces_safe":
                        raise QueryResolutionError("piece safety requires an explicit board phase")
                    return ordinary(values)
                if phase == "before":
                    selected = before_board or board
                elif phase == "after" and projected_board is not None:
                    selected = projected_board
                else:
                    raise QueryResolutionError(
                        "board phase is unknown or projection is unavailable"
                    )
                return BoardQueries(selected, side, budget).bindings()[name](values)

            queries[name] = phased

        def bounded_query(name: str, operation: Any) -> Any:
            """Wrap a trusted query with its traversal reservation.

            Args:
                name: Whitelisted operation identifier.
                operation: Registered read-only query.

            Returns:
                Query callable sharing the aggregate work ceiling.
            """

            def invoke(params: Mapping[str, Any]) -> Any:
                """Execute a query after reserving its bounded traversal work.

                Args:
                    params: Validated declarative parameters.

                Returns:
                    The query's independently validated JSON result.
                """
                self._charge(1)
                return operation(params)

            return invoke

        return {
            name: bounded_query(name, operation) for name, operation in queries.items()
        }, references

    def _offers(
        self, state: dict[str, Any], board: Board, side: int, now_ms: int
    ) -> dict[Move, tuple[PlannedEffect, ...]]:
        """Resolve bounded game-authored special intents before candidate authorization.

        Args:
            state: Observed authoritative snapshot.
            board: Corresponding board.
            side: Evaluating participant.
            now_ms: Trusted timestamp.

        Returns:
            Unique immutable intents mapped to their trusted auxiliary effect plans.

        Raises:
            QueryResolutionError: Offers are malformed, ambiguous or require recursive facts.
        """
        if not any(rule["hook"] == "available_moves" for rule in self.definition.rules):
            return {}
        effects = self._evaluate("available_moves", state, board, side, None, [], now_ms)
        offers: dict[Move, tuple[PlannedEffect, ...]] = {}
        for effect in effects:
            if effect.op != "offer_move":
                raise QueryResolutionError("available_moves may only emit bounded move offers")
            params = thaw_json(effect.params)
            move = Move(
                tuple(params["start"]),
                tuple(params["end"]),
                hops=tuple(tuple(square) for square in params.get("hops", [params["end"]])),
                promotion=params.get("promotion"),
            )
            if any(not board.is_within_bounds(*square) for square in (move.start_pos, *move.hops)):
                raise QueryResolutionError("offered coordinates are outside the board")
            piece = board.get_piece_at(move.start_pos)
            if piece is None or piece.getColor() != side:
                raise QueryResolutionError(
                    "offered source must belong to the evaluating participant"
                )
            if move in offers:
                raise QueryResolutionError("ambiguous duplicate move offers")
            self._charge(_json_work(params))
            offers[move] = tuple(
                PlannedEffect(item["op"], item["params"]) for item in params.get("effects", [])
            )
        return offers

    def _promotion(self, piece: Piece, move: Move, rows: int) -> str | None:
        """Derive promotion exclusively from configured rank and choice policy.

        Args:
            piece: Moving piece before transition.
            move: Intent carrying an optional selected kind.
            rows: Explicit configured board rows.

        Returns:
            Replacement kind or None when no promotion is due.

        Raises:
            TransitionError: Choice or capture-chain crowning boundary is invalid.
        """
        policy = self.definition.pieces[piece.getType()].get("promotion")
        far = 0 if piece.getColor() == 1 else rows - 1
        if policy and policy["stop_capture"] and any(square[0] == far for square in move.hops[:-1]):
            raise TransitionError("capture chain must stop on its configured crowning rank")
        if not policy or move.end_pos[0] != far:
            if move.promotion is not None:
                raise TransitionError("promotion is not available on this destination")
            return None
        if policy["mode"] == "automatic":
            if move.promotion is not None:
                raise TransitionError("automatic promotion does not accept a client choice")
            return policy["options"][0]
        if move.promotion not in policy["options"]:
            raise TransitionError("move requires one configured promotion choice")
        return move.promotion

    def _intents(
        self, start: tuple[int, int], hops: tuple[tuple[int, int], ...], piece: Piece, rows: int
    ) -> list[Move]:
        """Expand configured explicit choices without inventing piece identities.

        Args:
            start: Source coordinates.
            hops: Complete landing sequence.
            piece: Configured moving piece.
            rows: Board rows.

        Returns:
            One ordinary intent or each configured promotion-choice intent.
        """
        policy = self.definition.pieces[piece.getType()].get("promotion")
        far = 0 if piece.getColor() == 1 else rows - 1
        choices = (
            policy["options"]
            if policy and policy["mode"] == "choice" and hops[-1][0] == far
            else (None,)
        )
        return [Move(start, hops[-1], hops=hops, promotion=choice) for choice in choices]

    def _candidate(
        self,
        state: dict[str, Any],
        board: Board,
        move: Move,
        side: int,
        now_ms: int,
        offered_intents: Mapping[Move, tuple[PlannedEffect, ...]] | None = None,
    ) -> tuple[list[list[int]], tuple[PlannedEffect, ...]]:
        """Require exact geometry or a complete server-enumerated capture chain.

        Args:
            state: Position metadata.
            board: Isolated position.
            move: Immutable intent.
            side: Active side being authorized.
            now_ms: Trusted evaluation timestamp.
            offered_intents: Plans evaluated against exactly this observed state.

        Returns:
            Server-derived capture coordinates and offered auxiliary effects.

        Raises:
            TransitionError: Intent is incomplete, illegal or belongs to another side.
        """
        if any(not board.is_within_bounds(*square) for square in (move.start_pos, *move.hops)):
            raise TransitionError("move square is outside the configured board")
        piece = board.get_piece_at(move.start_pos)
        if piece is None or piece.getColor() != side:
            raise TransitionError("source does not belong to the active participant")
        self._promotion(piece, move, board.rows)
        offers = (
            self._offers(state, board, side, now_ms) if offered_intents is None else offered_intents
        )
        if move in offers:
            target = board.get_piece_at(move.end_pos)
            if target is not None and target.getColor() == side:
                raise TransitionError("offered destination cannot overwrite a friendly piece")
            return ([list(move.end_pos)] if target is not None else []), offers[move]
        spec = self.definition.pieces[piece.getType()]
        if "capture_policy" in spec:
            for route in self._paths(board, side):
                if (
                    tuple(route["start"]) == move.start_pos
                    and tuple(tuple(step["landing"]) for step in route["steps"]) == move.hops
                ):
                    return [step["captured"] for step in route["steps"]], ()
            if len(move.hops) != 1 or board.get_piece_at(move.end_pos) is not None:
                raise TransitionError("capture intent must contain one complete legal chain")
        elif len(move.hops) != 1:
            raise TransitionError("piece does not declare chained capture capability")
        self._charge(
            len(piece.getDirections() + piece.getAttackDirections()) * max(board.rows, board.cols)
        )
        if move.end_pos not in MoveValidator(board).get_geometric_moves(move.start_pos):
            raise TransitionError("move is not a configured geometric candidate")
        return ([list(move.end_pos)] if board.get_piece_at(move.end_pos) is not None else []), ()

    def _evaluate(
        self,
        hook: str,
        state: dict[str, Any],
        board: Board,
        side: int,
        move: Move | None,
        captures: list[list[int]],
        now_ms: int,
        counts: dict[str, int] | None = None,
        before_board: Board | None = None,
        projected_board: Board | None = None,
        action: dict[str, Any] | None = None,
        expired_side: int | None = None,
        event_actor: str | None = None,
    ) -> tuple[PlannedEffect, ...]:
        """Evaluate configured rules without mutating their inputs.

        Args:
            hook: Configured lifecycle hook.
            state: Isolated session data.
            board: Corresponding isolated board.
            side: Evaluation participant side.
            move: Optional candidate intent.
            captures: Derived capture coordinates.
            now_ms: Trusted timestamp.
            counts: Optional computed legal counts.
            before_board: Original board for explicit before-phase queries.
            projected_board: Isolated board after derived movement and effects.

        Returns:
            Immutable effects in declared order.
        """
        if not self._program.rules(hook):
            return ()
        queries, references = self._context(
            state,
            board,
            side,
            move,
            captures,
            now_ms,
            counts,
            before_board,
            projected_board,
            action,
            expired_side,
            event_actor,
        )
        return self._program.evaluate(hook, queries, references, self._charge).effects

    @staticmethod
    def _allowed(effects: tuple[PlannedEffect, ...]) -> bool:
        """Require an explicit permit and give every denial precedence.

        Args:
            effects: Validated move authorization effects.

        Returns:
            Whether configuration explicitly authorizes this candidate.

        Raises:
            TransitionError: Authorization attempts a mutation or outcome effect.
        """
        if any(effect.op not in {"permit", "deny", "record_event"} for effect in effects):
            raise TransitionError("move authorization cannot mutate a session")
        return any(effect.op == "permit" for effect in effects) and not any(
            effect.op == "deny" for effect in effects
        )

    def _complete_quest(self, state: dict[str, Any], player: str | int, quest_id: str) -> None:
        """Record at most one configured reward for an actual participant.

        Args:
            state: Isolated candidate state.
            player: Participant identity.
            quest_id: Configured quest identifier.

        Raises:
            TransitionError: Participant or quest does not belong to the session.
        """
        if type(player) is int and player in (-1, 1):
            player = state["participants"][str(player)]
        if player not in state["quest_progress"] or quest_id not in state["quest_progress"][player]:
            raise TransitionError("quest completion needs a configured participant objective")
        progress = state["quest_progress"][player][quest_id]
        progress.update(active=progress["target"], completed=True)

    def _effects(
        self, effects: tuple[PlannedEffect, ...], state: dict[str, Any], board: Board
    ) -> list[dict[str, Any]]:
        """Apply bounded effects only to an isolated candidate and board.

        Args:
            effects: Immutable validated effect plan.
            state: Candidate state that is discarded on any failure.
            board: Candidate board storage.

        Returns:
            Detached game-owned event payloads.

        Raises:
            TransitionError: An effect is invalid for the candidate position.
        """
        emitted: list[dict[str, Any]] = []
        for effect in effects:
            self._charge(_json_work(effect.params))
            params = thaw_json(effect.params)
            op = effect.op
            if op in {"set_state", "set_rights"}:
                field = "rule_state" if op == "set_state" else "special_rights"
                state[field][params["name"]] = params["value"]
            elif op == "set_target":
                value = params["value"]
                if value is not None and not board.is_within_bounds(*value):
                    raise TransitionError("temporary target is outside the board")
                state["temporary_targets"][params["name"]] = value
            elif op == "increment_state":
                value = state["rule_state"].get(params["name"], 0)
                if type(value) is not int:
                    raise TransitionError("increment requires integer rule state")
                state["rule_state"][params["name"]] = value + params["amount"]
            elif op == "record_event":
                emitted.append(params)
            elif op == "complete_quest":
                self._complete_quest(state, params["player"], params["quest"])
            elif op == "set_clock":
                players = state["participants"]
                if type(params["player"]) is int and params["player"] in (-1, 1):
                    params["player"] = players[str(params["player"])]
                side = next(
                    (side for side, identity in players.items() if identity == params["player"]),
                    None,
                )
                if side is None:
                    raise TransitionError("clock effect requires a participant identity")
                state["clocks"]["remaining_ms"][side] = params["seconds"] * 1000
            elif op in {"move_piece", "capture_piece", "replace_piece"}:
                fields = ("start", "end") if op == "move_piece" else ("square",)
                if any(not board.is_within_bounds(*params[field]) for field in fields):
                    raise TransitionError("effect square is outside the board")
                if op == "move_piece":
                    if board.get_piece_at(tuple(params["end"])) is not None:
                        raise TransitionError(
                            "movement effect needs an empty destination; capture explicitly"
                        )
                    if not board.move_piece(tuple(params["start"]), tuple(params["end"])):
                        raise TransitionError("configured movement effect cannot execute")
                else:
                    square = tuple(params["square"])
                    piece = board.get_piece_at(square)
                    if piece is None:
                        raise TransitionError("configured effect requires an occupied square")
                    if op == "capture_piece":
                        state["captured"].append(
                            {"kind": piece.getType(), "side": piece.getColor()}
                        )
                        state["events"][-1]["captured"].append(list(square))
                        state["halfmove_count"] = 0
                        board.set_piece_at(square, None)
                    else:
                        board.set_piece_at(
                            square, self._piece(params["kind"], piece.getColor(), True)
                        )
            elif op == "propose_outcome":
                continue
            else:
                raise TransitionError(f"effect is not valid in the transition hook: {op}")
        return emitted

    def _prepare_move(
        self,
        state: dict[str, Any],
        side: int,
        actor_id: str,
        expected_revision: int,
        action_id: str,
        move: Move,
        now_ms: int,
        *,
        enforce_clock: bool = True,
        offered_intents: Mapping[Move, tuple[PlannedEffect, ...]] | None = None,
        preview: bool = False,
    ) -> tuple[dict[str, Any], Board, list[list[int]], tuple[PlannedEffect, ...], dict[str, Any]]:
        """Prepare the same complete isolated transition for execution and legal previews.

        Args:
            state: Authoritative detached position; this input is never mutated.
            side: Selected participant side.
            actor_id: Identity attached to the preview or action.
            expected_revision: Base revision recorded with the action.
            action_id: Stable action identifier.
            move: Complete candidate intent.
            now_ms: Trusted evaluation timestamp.
            offered_intents: Plans owned by the observed-position enumeration.
            preview: Discard-only legality projection. Position serialization is
                unnecessary when no quest consumes the appended history entry.
            enforce_clock: Require action-time eligibility; position identity probes
                evaluate capture legality independently of the built-in clock deadline.

        Returns:
            Isolated state, board, captures, effects and event before outcome arbitration.

        Raises:
            TransitionError: Geometry, permission, clock or configured effects fail.
        """
        observed = state
        state = self._copy_state(state)
        elapsed = now_ms - state["clocks"]["anchor_ms"] if side == state["active_side"] else 0
        if enforce_clock and (elapsed < 0 or elapsed >= state["clocks"]["remaining_ms"][str(side)]):
            raise TransitionError("participant clock does not permit an action")
        before_board = self._board(state)
        board = self._board(state)
        captures, offered_effects = self._candidate(
            state, board, move, side, now_ms, offered_intents
        )
        moving_piece = board.get_piece_at(move.start_pos)
        promotion = self._promotion(moving_piece, move, board.rows)
        reset = bool(captures)
        for square in captures:
            captured = board.get_piece_at(tuple(square))
            state["captured"].append({"kind": captured.getType(), "side": captured.getColor()})
            board.set_piece_at(tuple(square), None)
        board.set_piece_at(move.start_pos, None)
        board.set_piece_at(move.end_pos, moving_piece)
        moving_piece.setMoved(True)
        state["board"] = self._placement(board)
        state["clocks"]["remaining_ms"][str(side)] -= elapsed
        state["clocks"]["remaining_ms"][str(side)] += state["clocks"]["increment_ms"]
        state["clocks"]["anchor_ms"] = now_ms
        state["active_side"] = -side
        state["halfmove_count"] = 0 if reset else state["halfmove_count"] + 1
        state["revision"] += 1
        event = {
            "revision": state["revision"],
            "expected_revision": expected_revision,
            "actor": actor_id,
            "action_id": action_id,
            "at_ms": now_ms,
            "move": move.to_json(),
            "captured": captures,
            "effects": [],
        }
        state["events"].append(event)
        state["temporary_targets"] = {name: None for name in state["temporary_targets"]}
        emitted = self._effects(offered_effects, state, board)
        if self.definition.halfmove_reset is not None:
            queries, references = self._context(
                observed,
                before_board,
                side,
                move,
                captures,
                now_ms,
                before_board=before_board,
                projected_board=board,
            )
            extra_reset = ConditionEvaluator(queries, references).evaluate(
                thaw_json(self.definition.halfmove_reset)
            )
            state["halfmove_count"] = (
                0 if captures or extra_reset else observed["halfmove_count"] + 1
            )
        if promotion is not None:
            board.set_piece_at(move.end_pos, self._piece(promotion, side, True))
        state["board"] = self._placement(board)
        effects = self._evaluate(
            "on_move_made",
            state,
            board,
            side,
            move,
            captures,
            now_ms,
            before_board=before_board,
            projected_board=board,
        )
        emitted.extend(self._effects(effects, state, board))
        authorization = self._evaluate(
            "permits_move",
            observed,
            before_board,
            side,
            move,
            captures,
            now_ms,
            before_board=before_board,
            projected_board=board,
        )
        if not self._allowed(authorization):
            raise TransitionError("configured rules deny this intent")
        emitted = (
            self._effects(
                tuple(effect for effect in authorization if effect.op == "record_event"),
                state,
                board,
            )
            + emitted
        )
        event["effects"] = emitted
        state["board"] = self._placement(board)
        if (not preview or self.definition.quests) and (
            self._evaluation is None or not self._evaluation.identity_probe_depth
        ):
            state["position_history"].append(self._position_key(state))
        if not self.definition.quests:
            return state, board, captures, effects, event
        queries, references = self._context(
            state,
            board,
            side,
            move,
            captures,
            now_ms,
            before_board=before_board,
            projected_board=board,
        )
        evaluator = ConditionEvaluator(queries, references)
        for quest in self.definition.quests:
            self._charge(_json_work(quest))
            if evaluator.evaluate(thaw_json(quest["when"])):
                self._complete_quest(state, actor_id, quest["id"])
        return state, board, captures, effects, event

    def _candidates(
        self,
        state: dict[str, Any],
        board: Board,
        side: int,
        now_ms: int,
        offered_intents: Mapping[Move, tuple[PlannedEffect, ...]] | None = None,
    ) -> list[Move]:
        """Build one bounded shared candidate set for authorization and identity probes.

        Args:
            state: Isolated observed snapshot.
            board: Corresponding board.
            side: Evaluating participant side.
            now_ms: Trusted query timestamp.
            offered_intents: Plans evaluated against this same observed position.

        Returns:
            Geometric, complete capture and declaratively offered intents.

        Raises:
            QueryResolutionError: Candidate or aggregate work bounds are exhausted.
        """
        candidates: list[Move] = []
        for record in state["board"]:
            if record["side"] != side:
                continue
            start = tuple(record["square"])
            piece = board.get_piece_at(start)
            self._charge(
                len(piece.getDirections() + piece.getAttackDirections())
                * max(board.rows, board.cols)
            )
            for end in MoveValidator(board).get_geometric_moves(start):
                if (
                    "capture_policy" in self.definition.pieces[record["kind"]]
                    and board.get_piece_at(end) is not None
                ):
                    continue
                self._charge()
                if len(candidates) >= 4096:
                    raise QueryResolutionError(
                        "candidate move enumeration exceeds bounded resources"
                    )
                for intent in self._intents(start, (end,), piece, board.rows):
                    if len(candidates) >= 4096:
                        raise QueryResolutionError(
                            "candidate move enumeration exceeds bounded resources"
                        )
                    candidates.append(intent)
        for route in self._paths(board, side):
            hops = tuple(tuple(step["landing"]) for step in route["steps"])
            self._charge(len(hops))
            if len(candidates) >= 4096:
                raise QueryResolutionError("candidate move enumeration exceeds bounded resources")
            for intent in self._intents(
                tuple(route["start"]), hops, board.get_piece_at(tuple(route["start"])), board.rows
            ):
                if len(candidates) >= 4096:
                    raise QueryResolutionError(
                        "candidate move enumeration exceeds bounded resources"
                    )
                candidates.append(intent)
        offers = (
            self._offers(state, board, side, now_ms) if offered_intents is None else offered_intents
        )
        for move in offers:
            if move not in candidates:
                if len(candidates) >= 4096:
                    raise QueryResolutionError(
                        "candidate move enumeration exceeds bounded resources"
                    )
                candidates.append(move)
        return candidates

    def _legal_moves(self, state: dict[str, Any], side: int, now_ms: int) -> list[Move]:
        """Enumerate configured candidates and require declarative authorization.

        Args:
            state: Detached position under evaluation.
            side: Evaluation participant side.
            now_ms: Trusted time for read-only rules.

        Returns:
            Complete authorized intents in stable order.
        """
        if state["outcome"] is not None:
            return []
        board = self._board(state)
        offered_intents = self._offers(state, board, side, now_ms)
        candidates = self._candidates(state, board, side, now_ms, offered_intents)
        legal: list[Move] = []
        for move in candidates:
            try:
                self._prepare_move(
                    state,
                    side,
                    state["participants"][str(side)],
                    state["revision"],
                    "legal-preview",
                    move,
                    now_ms,
                    offered_intents=offered_intents,
                    preview=True,
                )
            except TransitionError:
                continue
            legal.append(move)
        return legal

    def get_valid_moves(self) -> list[Move]:
        """Read configured legal intents without consuming time or changing state.

        Returns:
            Authorized intents for the active participant at the stored clock anchor.
        """
        with self._lock, self._operation():
            self._charge(_json_work(self._state))
            state = self._copy_state(self._state)
            return self._legal_moves(state, state["active_side"], state["clocks"]["anchor_ms"])

    def board_projection(self) -> Board:
        """Build a detached render-only board without sharing mutable engine facts."""
        with self._lock, self._operation():
            return self._board(self._state)

    def get_state(self) -> dict[str, Any]:
        """Return a detached complete session snapshot for durable storage.

        Returns:
            JSON-compatible configuration, state, clocks, quests and event history.
        """
        with self._lock:
            return thaw_json(self._state)

    @staticmethod
    def _action(action: Any) -> dict[str, Any]:
        """Parse a closed action DTO without accepting state or result assertions.

        Args:
            action: Untrusted JSON move, resignation, claim or timeout request.

        Returns:
            Detached canonical action data.

        Raises:
            TransitionError: Type, keys, claim or move intent is malformed.
        """
        if not isinstance(action, dict) or not isinstance(action.get("type"), str):
            raise TransitionError("action must be a typed JSON object")
        contracts = {
            "move": {"type", "move"},
            "resign": {"type"},
            "timeout": {"type"},
            "claim_draw": {"type", "claim", "intended_move"},
        }
        if action["type"] not in contracts or set(action) != contracts[action["type"]]:
            raise TransitionError("action has unknown or missing fields")
        result = dict(action)
        try:
            if action["type"] == "move":
                result["move"] = Move.from_json(action["move"]).to_json()
            elif action["type"] == "claim_draw":
                claim = action["claim"]
                if (
                    not isinstance(claim, str)
                    or not claim
                    or len(claim) > MAX_GAME_JSON_BYTES
                    or len(claim.encode("utf-8")) > MAX_GAME_JSON_BYTES
                ):
                    raise ValueError("claim must name a bounded configured outcome rule")
                if action["intended_move"] is not None:
                    result["intended_move"] = Move.from_json(action["intended_move"]).to_json()
            return thaw_json(freeze_json(result))
        except (ValueError, TypeError, KeyError) as error:
            raise TransitionError(f"invalid action intent: {error}") from error

    def submit(
        self, actor_id: str, expected_revision: int, action_id: str, move: Move, now_ms: int
    ) -> dict[str, Any]:
        """Submit a move through the shared authoritative action coordinator.

        Args:
            actor_id: Authenticated participant identity.
            expected_revision: Revision observed when constructing the request.
            action_id: Stable retry identifier.
            move: Immutable complete move intent.
            now_ms: Trusted server timestamp in milliseconds.

        Returns:
            Detached accepted move event, retaining its snapshot version 1 shape.

        Raises:
            TransitionError: Identity, revision, intent, clock or effects are invalid.
            QueryResolutionError: Required rule facts or evaluation resources are unavailable.
        """
        if not isinstance(move, Move):
            raise TransitionError("move intent is required")
        return self.submit_action(
            actor_id, expected_revision, action_id, {"type": "move", "move": move.to_json()}, now_ms
        )

    def _result(
        self, effects: tuple[PlannedEffect, ...], state: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Resolve proposals and bind winners to actual session identities.

        Args:
            effects: Validated outcome proposals.
            state: Isolated candidate session.

        Returns:
            Canonical result data or None when no proposal exists.

        Raises:
            TransitionError: A winner is not a participant.
            QueryResolutionError: Proposals conflict or are malformed.
        """
        outcome = resolve_outcome(effects)
        if outcome is None:
            return None
        result = asdict(outcome)
        winner = result["winner"]
        if type(winner) is int and winner in (-1, 1):
            result["winner"] = state["participants"][str(winner)]
        elif winner is not None and winner not in state["participants"].values():
            raise TransitionError("outcome winner must be a participant")
        return result

    def _terminal_action(
        self,
        state: dict[str, Any],
        actor_id: str,
        expected_revision: int,
        action_id: str,
        action: dict[str, Any],
        now_ms: int,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Prepare an explicit configured terminal action without committing a claim probe.

        Args:
            state: Detached observed authoritative session.
            actor_id: Verified submitting identity.
            expected_revision: Observed revision.
            action_id: Stable request identifier.
            action: Canonical resignation, draw-claim or timeout DTO.
            now_ms: Trusted server timestamp.

        Returns:
            Isolated terminal state and its exact request event.

        Raises:
            TransitionError: Turn, clock, claim or terminal eligibility fails.
            QueryResolutionError: Required facts, proposals or resource bounds fail.
        """
        active = state["active_side"]
        side = next(
            int(key) for key, identity in state["participants"].items() if identity == actor_id
        )
        elapsed = now_ms - state["clocks"]["anchor_ms"]
        if elapsed < 0:
            raise TransitionError("authoritative timestamp cannot run backwards")
        expired = elapsed >= state["clocks"]["remaining_ms"][str(active)]
        if action["type"] == "timeout" and not expired:
            raise TransitionError("timeout requires the authoritative active clock deadline")
        if action["type"] == "claim_draw" and (side != active or expired):
            raise TransitionError("draw claim requires the active participant before expiry")
        original_board = self._board(state)
        evaluation = self._copy_state(state)
        board = original_board
        intended = None
        captures: list[list[int]] = []
        projected_effects: tuple[PlannedEffect, ...] = ()
        if action["type"] == "claim_draw" and action["intended_move"] is not None:
            intended = Move.from_json(action["intended_move"])
            evaluation, board, captures, projected_effects, _ = self._prepare_move(
                state, side, actor_id, expected_revision, action_id, intended, now_ms
            )
        state["clocks"]["remaining_ms"][str(active)] = max(
            0, state["clocks"]["remaining_ms"][str(active)] - elapsed
        )
        state["clocks"]["anchor_ms"] = now_ms
        state["revision"] += 1
        event = {
            "revision": state["revision"],
            "expected_revision": expected_revision,
            "actor": actor_id,
            "action_id": action_id,
            "at_ms": now_ms,
            "move": None,
            "captured": [],
            "effects": [],
            "outcome": None,
            "action": action,
        }
        state["events"].append(event)
        evaluation["events"] = thaw_json(freeze_json(state["events"]))
        evaluation["revision"] = state["revision"]
        evaluation["clocks"] = thaw_json(freeze_json(state["clocks"]))
        counts = {
            "active": len(self._legal_moves(evaluation, side, now_ms)),
            "opponent": len(self._legal_moves(evaluation, -side, now_ms)),
        }
        expired_side = active if expired else None
        if action["type"] == "claim_draw":
            selected = [
                rule
                for rule in self.definition.rules
                if rule["hook"] == "outcome" and rule["id"] == action["claim"]
            ]
            if len(selected) != 1:
                raise TransitionError("draw claim must name one configured outcome rule")
            queries, references = self._context(
                evaluation,
                board,
                side,
                intended,
                captures,
                now_ms,
                counts,
                original_board,
                board,
                action,
                expired_side,
            )
            self._charge(_json_work(selected))
            plan = HookInterpreter(thaw_json(selected), queries, references).evaluate("outcome")
            claimed = self._result(plan.effects, state)
            if (
                not plan.matched_rule_ids
                or claimed is None
                or claimed["kind"] != "draw"
                or claimed["winner"] is not None
            ):
                raise TransitionError("named draw claim is not eligible")
        terminal = self._evaluate(
            "outcome",
            evaluation,
            board,
            side,
            intended,
            captures,
            now_ms,
            counts,
            original_board,
            board,
            action,
            expired_side,
        )
        if any(effect.op != "propose_outcome" for effect in terminal):
            raise TransitionError("terminal outcome hook may only propose results")
        result = self._result((*projected_effects, *terminal), state)
        if result is None:
            raise TransitionError("terminal action requires a configured result")
        if action["type"] == "claim_draw" and (
            result["kind"] != "draw" or result["winner"] is not None
        ):
            raise TransitionError("draw claim is overridden by a decisive proposal")
        state["outcome"] = result
        event["outcome"] = result
        return state, event

    def submit_action(
        self,
        actor_id: str,
        expected_revision: int,
        action_id: str,
        action: dict[str, Any],
        now_ms: int,
    ) -> dict[str, Any]:
        """Authorize one typed action and publish atomically, or return its exact retry.

        Args:
            actor_id: Authenticated participant identity supplied by the host.
            expected_revision: Revision observed when creating the action.
            action_id: Stable identifier reused only with an identical request.
            action: Exact object: type/move for move; type alone for resign or
                timeout; type/claim/intended_move for claim_draw. Claim names one
                configured outcome rule; intended_move is a move intent or null.
                Terminal outcomes require configured proposals. Move events retain
                the version-1 envelope; terminal events add action with a null move.
            now_ms: Trusted server timestamp; retry timestamps do not alter state.

        Returns:
            Detached accepted event with a durable result where configured.

        Raises:
            TransitionError: Identity, turn, revision, clock or request is invalid.
            QueryResolutionError: Rule data or trusted evaluation resources are invalid.
        """
        self._identifier(actor_id)
        self._identifier(action_id)
        self._timestamp(now_ms)
        if type(expected_revision) is not int or expected_revision < 0:
            raise TransitionError("expected revision must be a nonnegative integer")
        request = self._action(action)
        with self._lock, self._operation():
            self._charge(_json_work(self._state) + _json_work(request))
            state = self._copy_state(self._state)
            if actor_id not in state["participants"].values():
                raise TransitionError("actor is not a game participant")
            for event in state["events"]:
                self._charge()
                saved_request = event.get("action", {"type": "move", "move": event["move"]})
                if event["action_id"] == action_id:
                    if (
                        event["actor"] == actor_id
                        and event["expected_revision"] == expected_revision
                        and thaw_json(saved_request) == request
                    ):
                        return thaw_json(freeze_json(event))
                    raise TransitionError("action identifier has a conflicting request")
            if expected_revision != state["revision"]:
                raise TransitionError("stale game revision")
            if state["outcome"] is not None:
                raise TransitionError("game has a terminal result")
            if len(state["events"]) >= MAX_EVENTS:
                raise TransitionError("session event limit reached")
            if request["type"] != "move":
                state, event = self._terminal_action(
                    state, actor_id, expected_revision, action_id, request, now_ms
                )
            else:
                move = Move.from_json(request["move"])
                side = state["active_side"]
                if actor_id != state["participants"][str(side)]:
                    raise TransitionError("actor does not control the active turn")
                elapsed = now_ms - state["clocks"]["anchor_ms"]
                if elapsed < 0:
                    raise TransitionError("authoritative timestamp cannot run backwards")
                if elapsed >= state["clocks"]["remaining_ms"][str(side)]:
                    raise TransitionError("active participant clock has expired")
                state, board, captures, effects, event = self._prepare_move(
                    state, side, actor_id, expected_revision, action_id, move, now_ms
                )
                counts = None
                if any(rule["hook"] == "outcome" for rule in self.definition.rules):
                    counts = {
                        "active": len(self._legal_moves(state, -side, now_ms)),
                        "opponent": len(self._legal_moves(state, side, now_ms)),
                    }
                terminal = self._evaluate(
                    "outcome",
                    state,
                    board,
                    -side,
                    move,
                    captures,
                    now_ms,
                    counts,
                    projected_board=board,
                    event_actor=actor_id,
                )
                if any(effect.op != "propose_outcome" for effect in terminal):
                    raise TransitionError("outcome hook must only propose terminal results")
                state["outcome"] = self._result((*effects, *terminal), state)
                event["outcome"] = state["outcome"]
            self._charge(_json_work(state))
            encoded = json.dumps(thaw_json(state), allow_nan=False, separators=(",", ":"))
            if len(encoded.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
                raise TransitionError("snapshot exceeds bounded persistence size")
            self._state = freeze_json(state)
            return thaw_json(freeze_json(event))

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> GameManager:
        """Recover authoritative state by replay, rejecting inconsistent claims.

        Args:
            snapshot: Complete JSON snapshot read from trusted durable storage.

        Returns:
            An independently reconstructed session with identical observable state.

        Raises:
            TransitionError: Snapshot envelope or replayed state is inconsistent.
        """
        try:
            data = thaw_json(freeze_json(snapshot))
            encoded = json.dumps(data, allow_nan=False, separators=(",", ":"))
            if len(encoded.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
                raise TransitionError("snapshot exceeds bounded persistence size")
            if data["version"] != 1 or type(data["version"]) is not int:
                raise TransitionError("unsupported session snapshot version")
            participants = data["participants"]
            if set(participants) != {"1", "-1"}:
                raise TransitionError("snapshot must contain exactly two participant sides")
            restored = cls(
                validate_definition(data["config"], "<snapshot>"),
                data["game_id"],
                (participants["1"], participants["-1"]),
                data["started_at_ms"],
            )
            if not isinstance(data["events"], list) or len(data["events"]) > MAX_EVENTS:
                raise TransitionError("snapshot requires bounded durable event history")
            aggregate = EvaluationBudget(MAX_REPLAY_WORK)
            aggregate.consume(_json_work(data))
            for event in data["events"]:
                # Each action retains exactly its submission ceiling and isolated cache.
                # The parent cannot reset and is derived from all supported action ceilings.
                child = EvaluationBudget(MAX_EVALUATION_WORK, parent=aggregate)
                with restored._lock, restored._operation(child):
                    restored.submit_action(
                        event["actor"],
                        event["expected_revision"],
                        event["action_id"],
                        event.get("action", {"type": "move", "move": event["move"]}),
                        event["at_ms"],
                    )
            recovered = json.dumps(restored.get_state(), sort_keys=True, allow_nan=False)
            supplied = json.dumps(data, sort_keys=True, allow_nan=False)
            if recovered != supplied:
                raise TransitionError("snapshot does not agree with authoritative event replay")
            return restored
        except (ValueError, TypeError, KeyError, RecursionError, OverflowError) as error:
            raise TransitionError(f"invalid session snapshot: {error}") from error
