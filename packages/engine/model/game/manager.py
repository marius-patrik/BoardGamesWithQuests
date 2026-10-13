"""Authoritative, replayable JSON game transitions with isolated effect execution.

Every accepted intent produces one revision and one durable event. Identity,
turn, candidate legality and every configured effect are checked before publishing
new state. Persistence adapters must additionally enforce database compare-and-swap.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
import json
from threading import RLock
from typing import Any

from engine.model.game.board import Board
from engine.model.game.board_queries import BoardQueries
from engine.model.game.capture_geometry import CaptureEnumerator, CapturePolicy
from engine.model.game.conditions import ConditionEvaluator, QueryResolutionError
from engine.model.game.configuration import (
    GameDefinition,
    board_from_definition,
    validate_definition,
)
from engine.model.game.hooks import HookInterpreter, PlannedEffect
from engine.model.game.move import Move
from engine.model.game.outcomes import resolve_outcome
from engine.model.game.schema import freeze_json, thaw_json
from engine.model.game.snapshot_queries import SnapshotQueries
from engine.model.game.validator import MoveValidator
from engine.model.pieces.piece import Piece

MAX_EVENTS = 4096
MAX_SNAPSHOT_BYTES = 4194304


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
        initial = definition.clock["initial_seconds"] * 1000
        state: dict[str, Any] = {
            "version": 1,
            "game_id": game_id,
            "config": config,
            "participants": {"1": participant_ids[0], "-1": participant_ids[1]},
            "started_at_ms": started_at_ms,
            "active_side": 1,
            "board": self._placement(board_from_definition(definition)),
            "captured": [],
            "rule_state": {},
            "special_rights": {},
            "temporary_targets": {},
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

    @staticmethod
    def _placement(board: Board) -> list[dict[str, Any]]:
        """Serialize pieces in stable row-major order, including movement rights.

        Args:
            board: Isolated board storage.

        Returns:
            Detached JSON piece records.
        """
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
            side,
            kind,
            vectors("moves"),
            vectors("attacks"),
            spec["jump"],
            kind,
            spec["repeat"],
            vectors("initial_moves"),
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
    def _position_key(state: Mapping[str, Any]) -> str:
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

    def _paths(self, board: Board, side: int) -> list[dict[str, Any]]:
        """Enumerate complete capture chains only for pieces declaring that policy.

        Args:
            board: Position under evaluation.
            side: Participant side.

        Returns:
            Complete ordered routes from configured capture policies.

        Raises:
            TransitionError: Enumeration exceeds bounded search resources.
        """
        routes: list[dict[str, Any]] = []
        for record in self._placement(board):
            if record["side"] != side:
                continue
            spec = self.definition.pieces[record["kind"]]
            if "capture_policy" in spec:
                routes.extend(
                    CaptureEnumerator(board).enumerate(
                        tuple(record["square"]),
                        CapturePolicy.from_json(spec["capture_policy"]),
                    )
                )
            if len(routes) > 128:
                raise TransitionError("capture path result exceeds bounded resources")
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
            "promotion_options": {"active": [], "opponent": []},
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
            "position_key": self._position_key(state),
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
        return (
            {
                **BoardQueries(board, side).bindings(),
                **SnapshotQueries(query_state).bindings(),
                "turn": BoardQueries(board, state["active_side"]).turn,
            },
            references,
        )

    def _candidate(
        self, state: dict[str, Any], board: Board, move: Move, side: int
    ) -> list[list[int]]:
        """Require exact geometry or a complete server-enumerated capture chain.

        Args:
            state: Position metadata.
            board: Isolated position.
            move: Immutable intent.
            side: Active side being authorized.

        Returns:
            Captured coordinates derived solely from board state.

        Raises:
            TransitionError: Intent is incomplete, illegal or belongs to another side.
        """
        if any(not board.is_within_bounds(*square) for square in (move.start_pos, *move.hops)):
            raise TransitionError("move square is outside the configured board")
        piece = board.get_piece_at(move.start_pos)
        if piece is None or piece.getColor() != side:
            raise TransitionError("source does not belong to the active participant")
        if move.promotion is not None:
            raise TransitionError("promotion requires configured move offers")
        spec = self.definition.pieces[piece.getType()]
        if "capture_policy" in spec:
            for route in self._paths(board, side):
                if (
                    tuple(route["start"]) == move.start_pos
                    and tuple(tuple(step["landing"]) for step in route["steps"]) == move.hops
                ):
                    return [step["captured"] for step in route["steps"]]
            if len(move.hops) != 1 or board.get_piece_at(move.end_pos) is not None:
                raise TransitionError("capture intent must contain one complete legal chain")
        elif len(move.hops) != 1:
            raise TransitionError("piece does not declare chained capture capability")
        if move.end_pos not in MoveValidator(board).get_geometric_moves(move.start_pos):
            raise TransitionError("move is not a configured geometric candidate")
        return [list(move.end_pos)] if board.get_piece_at(move.end_pos) is not None else []

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

        Returns:
            Immutable effects in declared order.
        """
        queries, references = self._context(state, board, side, move, captures, now_ms, counts)
        return (
            HookInterpreter(thaw_json(self.definition.rules), queries, references)
            .evaluate(hook)
            .effects
        )

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
            params = thaw_json(effect.params)
            op = effect.op
            if op in {"set_state", "set_rights"}:
                field = "rule_state" if op == "set_state" else "special_rights"
                state[field][params["name"]] = params["value"]
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

        Returns:
            Isolated state, board, captures, effects and event before outcome arbitration.

        Raises:
            TransitionError: Geometry, permission, clock or configured effects fail.
        """
        state = thaw_json(freeze_json(state))
        elapsed = now_ms - state["clocks"]["anchor_ms"] if side == state["active_side"] else 0
        if elapsed < 0 or elapsed >= state["clocks"]["remaining_ms"][str(side)]:
            raise TransitionError("participant clock does not permit an action")
        board = self._board(state)
        captures = self._candidate(state, board, move, side)
        authorization = self._evaluate("permits_move", state, board, side, move, captures, now_ms)
        if not self._allowed(authorization):
            raise TransitionError("configured rules deny this intent")
        moving_piece = board.get_piece_at(move.start_pos)
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
        state["halfmove_count"] = 0 if captures else state["halfmove_count"] + 1
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
        effects = self._evaluate("on_move_made", state, board, side, move, captures, now_ms)
        emitted = self._effects(
            tuple(effect for effect in authorization if effect.op == "record_event"),
            state,
            board,
        )
        emitted.extend(self._effects(effects, state, board))
        event["effects"] = emitted
        state["board"] = self._placement(board)
        state["position_history"].append(self._position_key(state))
        queries, references = self._context(state, board, side, move, captures, now_ms)
        evaluator = ConditionEvaluator(queries, references)
        for quest in self.definition.quests:
            if evaluator.evaluate(thaw_json(quest["when"])):
                self._complete_quest(state, actor_id, quest["id"])
        return state, board, captures, effects, event

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
        candidates: list[Move] = []
        for record in state["board"]:
            if record["side"] != side:
                continue
            start = tuple(record["square"])
            for end in MoveValidator(board).get_geometric_moves(start):
                if (
                    "capture_policy" in self.definition.pieces[record["kind"]]
                    and board.get_piece_at(end) is not None
                ):
                    continue
                candidates.append(Move(start, end))
        for route in self._paths(board, side):
            hops = tuple(tuple(step["landing"]) for step in route["steps"])
            candidates.append(Move(tuple(route["start"]), hops[-1], hops))
        if len(candidates) > 4096:
            raise TransitionError("candidate move enumeration exceeds bounded resources")
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
        with self._lock:
            state = thaw_json(self._state)
            return self._legal_moves(state, state["active_side"], state["clocks"]["anchor_ms"])

    def get_state(self) -> dict[str, Any]:
        """Return a detached complete session snapshot for durable storage.

        Returns:
            JSON-compatible configuration, state, clocks, quests and event history.
        """
        with self._lock:
            return thaw_json(self._state)

    def submit(
        self,
        actor_id: str,
        expected_revision: int,
        action_id: str,
        move: Move,
        now_ms: int,
    ) -> dict[str, Any]:
        """Authorize and atomically publish one move, or return its exact retry.

        Args:
            actor_id: Authenticated identity supplied by the trusted server.
            expected_revision: Revision observed when the intent was created.
            action_id: Stable client identifier reused only for the same request.
            move: Complete immutable move intent.
            now_ms: Trusted server timestamp; retry timestamps do not recharge clocks.

        Returns:
            Detached event recording the accepted action and resulting revision.

        Raises:
            TransitionError: Identity, revision, turn, clock, intent or effects fail.
            QueryResolutionError: Required configured queries cannot safely resolve.
        """
        self._identifier(actor_id)
        self._identifier(action_id)
        self._timestamp(now_ms)
        if (
            type(expected_revision) is not int
            or expected_revision < 0
            or not isinstance(move, Move)
        ):
            raise TransitionError("revision and move intent are required")
        with self._lock:
            state = thaw_json(self._state)
            if actor_id not in state["participants"].values():
                raise TransitionError("actor is not a game participant")
            for event in state["events"]:
                if event["action_id"] == action_id:
                    if (
                        event["actor"] == actor_id
                        and event["expected_revision"] == expected_revision
                        and event["move"] == move.to_json()
                    ):
                        return thaw_json(freeze_json(event))
                    raise TransitionError("action identifier has a conflicting request")
            side = state["active_side"]
            if expected_revision != state["revision"]:
                raise TransitionError("stale game revision")
            if state["outcome"] is not None:
                raise TransitionError("game has a terminal result")
            if actor_id != state["participants"][str(side)]:
                raise TransitionError("actor does not control the active turn")
            elapsed = now_ms - state["clocks"]["anchor_ms"]
            if elapsed < 0:
                raise TransitionError("authoritative timestamp cannot run backwards")
            if elapsed >= state["clocks"]["remaining_ms"][str(side)]:
                raise TransitionError("active participant clock has expired")
            if len(state["events"]) >= MAX_EVENTS:
                raise TransitionError("session event limit reached")
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
                "outcome", state, board, -side, move, captures, now_ms, counts
            )
            if any(effect.op != "propose_outcome" for effect in terminal):
                raise TransitionError("outcome hook must only propose terminal results")
            outcome = resolve_outcome((*effects, *terminal))
            if outcome is not None:
                result = asdict(outcome)
                winner = result["winner"]
                if type(winner) is int and winner in (-1, 1):
                    result["winner"] = state["participants"][str(winner)]
                elif winner is not None and winner not in state["participants"].values():
                    raise TransitionError("outcome winner must be a participant")
                state["outcome"] = result
            event["outcome"] = state["outcome"]
            encoded = json.dumps(state, allow_nan=False, separators=(",", ":"))
            if len(encoded.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
                raise TransitionError("snapshot exceeds bounded persistence size")
            frozen = freeze_json(state)
            self._state = frozen
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
            for event in data["events"]:
                restored.submit(
                    event["actor"],
                    event["expected_revision"],
                    event["action_id"],
                    Move.from_json(event["move"]),
                    event["at_ms"],
                )
            recovered = json.dumps(restored.get_state(), sort_keys=True, allow_nan=False)
            supplied = json.dumps(data, sort_keys=True, allow_nan=False)
            if recovered != supplied:
                raise TransitionError("snapshot does not agree with authoritative event replay")
            return restored
        except (ValueError, TypeError, KeyError, RecursionError, OverflowError) as error:
            raise TransitionError(f"invalid session snapshot: {error}") from error
