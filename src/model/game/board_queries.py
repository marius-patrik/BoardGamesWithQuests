"""Read-only game-neutral JSON query primitives backed by an explicit board."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

from model.game.board import Board
from model.game.conditions import QueryResolutionError
from model.game.capture_policy import EvaluationBudget, MAX_EVALUATION_WORK
from model.game.validator import MoveValidator


class BoardQueries:
    """Expose verified basic board facts, without game-name branches."""

    def __init__(
        self, board: Board, active_side: int, budget: EvaluationBudget | None = None
    ) -> None:
        """Bind an explicit participant and shared query traversal budget.

        Args:
            board: Isolated position under evaluation.
            active_side: Explicit evaluating side.
            budget: Shared trusted operation counter, or independent query ceiling.

        Raises:
            QueryResolutionError: The side selector is invalid.
        """
        if active_side not in (1, -1) or type(active_side) is not int:
            raise QueryResolutionError("active side must be 1 or -1")
        self._board = board
        self._active_side = active_side
        self._budget = budget if budget is not None else EvaluationBudget(MAX_EVALUATION_WORK)

    def _square(self, value: Any) -> tuple[int, int]:
        """Parse a JSON coordinate, never Python tuples or implicit defaults."""
        if (
            not isinstance(value, list)
            or len(value) != 2
            or any(type(coordinate) is not int for coordinate in value)
            or not self._board.is_within_bounds(value[0], value[1])
        ):
            raise QueryResolutionError("square must be an in-bounds JSON [row, column]")
        return (value[0], value[1])

    @staticmethod
    def _fields(params: Mapping[str, Any], required: set[str]) -> None:
        """Reject unknown, missing or game-specific private parameters."""
        if set(params) != required:
            raise QueryResolutionError(f"query needs exactly these fields: {sorted(required)}")

    def piece_at(self, params: Mapping[str, Any]) -> dict[str, Any] | None:
        """Return a value snapshot rather than exposing a mutable Piece."""
        self._fields(params, {"square"})
        square = self._square(params["square"])
        piece = self._board.get_piece_at(square)
        if piece is None:
            return None
        return {
            "kind": str(piece.getType()),
            "side": piece.getColor(),
            "moved": piece.hasMoved(),
        }

    def board_dimension(self, params: Mapping[str, Any]) -> int:
        """Read explicit rows or columns, rather than inferring an 8×8 board."""
        self._fields(params, {"axis"})
        axis = params["axis"]
        if axis == "rows":
            return self._board.rows
        if axis == "columns":
            return self._board.cols
        raise QueryResolutionError("axis must be rows or columns")

    def turn(self, params: Mapping[str, Any]) -> int:
        """Read the active side from an authoritative session snapshot."""
        self._fields(params, set())
        return self._active_side

    def path_clear(self, params: Mapping[str, Any]) -> bool:
        """Check a straight geometric ray, independently of game legality.

        A ray may run horizontally, vertically or diagonally. Both source and
        target are excluded: an occupied destination must remain capturable.
        A non-straight offset cannot be a clear ray.
        """
        self._fields(params, {"source", "target"})
        start = self._square(params["source"])
        end = self._square(params["target"])
        dr, dc = end[0] - start[0], end[1] - start[1]
        if (dr == 0 and dc == 0) or not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
            return False
        steps = math.gcd(abs(dr), abs(dc))
        step_r, step_c = dr // steps, dc // steps
        self._budget.consume(steps)
        return all(
            self._board.get_piece_at((start[0] + step_r * i, start[1] + step_c * i)) is None
            for i in range(1, steps)
        )

    def pieces_matching(self, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Enumerate pieces in stable row-major order with JSON-only filters."""
        if not set(params).issubset({"side", "kind"}):
            raise QueryResolutionError("pieces_matching accepts only side and kind")
        side = params.get("side")
        if side == "active":
            side = self._active_side
        elif side == "opponent":
            side = -self._active_side
        elif side is not None and (type(side) is not int or side not in (-1, 1)):
            raise QueryResolutionError("invalid piece side selector")
        kind = params.get("kind")
        if kind is not None and (not isinstance(kind, str) or not kind):
            raise QueryResolutionError("piece kind must be a nonempty string")
        self._budget.consume(self._board.rows * self._board.cols)
        found: list[dict[str, Any]] = []
        for row in range(self._board.rows):
            for col in range(self._board.cols):
                piece = self._board.get_piece_at((row, col))
                if piece is None:
                    continue
                if side is not None and piece.getColor() != side:
                    continue
                if kind is not None and piece.getType() != kind:
                    continue
                found.append(
                    {
                        "square": [row, col],
                        "kind": str(piece.getType()),
                        "side": piece.getColor(),
                        "moved": piece.hasMoved(),
                    }
                )
                if len(found) > 128:
                    raise QueryResolutionError("query exceeds the bounded JSON result size")
        return found

    def squares_attacked(self, params: Mapping[str, Any]) -> bool:
        """Evaluate generic geometric attack vectors, not game-legal checks."""
        self._fields(params, {"target", "by_side"})
        target = self._square(params["target"])
        side = params["by_side"]
        if side == "active":
            side = self._active_side
        elif side == "opponent":
            side = -self._active_side
        elif type(side) is not int or side not in (-1, 1):
            raise QueryResolutionError("invalid attacking side")
        self._reserve_attacks(side)
        return MoveValidator(self._board).is_square_attacked(target, side)

    def _reserve_attacks(self, side: int) -> None:
        """Reserve complete attack traversal before scanning vectors and rays.

        Args:
            side: Explicit attacking side.

        Raises:
            QueryResolutionError: Aggregate work cannot cover the traversal.
        """
        self._budget.consume(2 * self._board.rows * self._board.cols)
        cost = 0
        for row in range(self._board.rows):
            for col in range(self._board.cols):
                piece = self._board.get_piece_at((row, col))
                if piece is not None and piece.getColor() == side:
                    cost += len(piece.getAttackDirections() or ()) * (
                        min(piece.getMaxSteps(), max(self._board.rows, self._board.cols))
                        if piece.getMaxSteps() is not None
                        else max(self._board.rows, self._board.cols)
                    )
        self._budget.consume(cost)

    def integer(self, params: Mapping[str, Any]) -> int:
        """Compute one whitelisted bounded integer operation from data.

        Args:
            params: Exact operation, left and right; operands are signed int64 values.

        Returns:
            Signed int64 addition, subtraction or floor-division result.

        Raises:
            QueryResolutionError: Operation, operand, divisor or result is invalid.
        """
        self._fields(params, {"operation", "left", "right"})
        left, right = params["left"], params["right"]
        if any(type(value) is not int or not -(2**63) <= value < 2**63 for value in (left, right)):
            raise QueryResolutionError("integer query requires signed int64 operands")
        operation = params["operation"]
        if operation == "add":
            result = left + right
        elif operation == "subtract":
            result = left - right
        elif operation == "floor_divide" and right != 0:
            result = left // right
        else:
            raise QueryResolutionError("integer operation or divisor is invalid")
        if not -(2**63) <= result < 2**63:
            raise QueryResolutionError("integer result exceeds signed int64")
        return result

    def square_offset(self, params: Mapping[str, Any]) -> list[int] | None:
        """Translate one in-bounds square by a bounded data offset.

        Args:
            params: Exact square and integer-pair offset.

        Returns:
            In-bounds translated square, or null when the result is outside the board.

        Raises:
            QueryResolutionError: Source or offset is malformed.
        """
        self._fields(params, {"square", "offset"})
        square = self._square(params["square"])
        offset = params["offset"]
        if (
            not isinstance(offset, list)
            or len(offset) != 2
            or any(type(axis) is not int or not -255 <= axis <= 255 for axis in offset)
        ):
            raise QueryResolutionError("square offset must be a bounded integer pair")
        result = [square[0] + offset[0], square[1] + offset[1]]
        return result if self._board.is_within_bounds(*result) else None

    def json_value(self, params: Mapping[str, Any]) -> Any:
        """Read a bounded path from JSON data without attribute or executable access.

        Args:
            params: Exact value and nonempty path of at most four text keys or indices.

        Returns:
            Selected JSON value or null for missing keys, indices or container mismatch.

        Raises:
            QueryResolutionError: Path keys or indices are malformed.
        """
        self._fields(params, {"value", "path"})
        path = params["path"]
        if not isinstance(path, list) or not 1 <= len(path) <= 4:
            raise QueryResolutionError("JSON value path must have one to four components")
        if any(
            not (
                (type(key) is int and -1 <= key <= 127)
                or (isinstance(key, str) and 1 <= len(key) <= 128)
            )
            for key in path
        ):
            raise QueryResolutionError("JSON path components must be bounded keys or indices")
        value = params["value"]
        for key in path:
            if type(key) is int and -1 <= key <= 127:
                if not isinstance(value, list) or not value or key >= len(value):
                    return None
                value = value[key]
            elif isinstance(key, str) and 1 <= len(key) <= 128:
                if not isinstance(value, dict) or key not in value:
                    return None
                value = value[key]
            else:
                raise QueryResolutionError("JSON path components must be bounded keys or indices")
        return value

    def pieces_safe(self, params: Mapping[str, Any]) -> bool:
        """Check all pieces with one configured role against opposing geometric attacks.

        Args:
            params: Exact configured kind and active/opponent or explicit side.

        Returns:
            False for a missing role or any attacked matching piece; otherwise True.

        Raises:
            QueryResolutionError: Parameters or selectors are invalid.
        """
        self._fields(params, {"kind", "side"})
        records = self.pieces_matching(params)
        if not records:
            return False
        for record in records:
            self._reserve_attacks(-record["side"])
        return all(
            not MoveValidator(self._board).is_square_attacked(
                tuple(record["square"]), -record["side"]
            )
            for record in records
        )

    def bindings(self) -> dict[str, Callable[[Mapping[str, Any]], Any]]:
        """Register only the implemented read-only primitives."""
        return {
            "pieces_safe": self.pieces_safe,
            "integer": self.integer,
            "json_value": self.json_value,
            "square_offset": self.square_offset,
            "piece_at": self.piece_at,
            "board_dimension": self.board_dimension,
            "turn": self.turn,
            "path_clear": self.path_clear,
            "pieces_matching": self.pieces_matching,
            "squares_attacked": self.squares_attacked,
        }
