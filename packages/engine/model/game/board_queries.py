"""Read-only game-neutral JSON query primitives backed by an explicit board."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

from engine.model.game.board import Board
from engine.model.game.conditions import QueryResolutionError
from engine.model.game.validator import MoveValidator


class BoardQueries:
    """Expose verified basic board facts, without game-name branches."""

    def __init__(self, board: Board, active_side: int):
        """Bind an explicit immutable turn identity to the current board."""
        if active_side not in (1, -1) or type(active_side) is not int:
            raise QueryResolutionError("active side must be 1 or -1")
        self._board = board
        self._active_side = active_side

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
        return MoveValidator(self._board).is_square_attacked(target, side)

    def bindings(self) -> dict[str, Callable[[Mapping[str, Any]], Any]]:
        """Register only the implemented read-only primitives."""
        return {
            "piece_at": self.piece_at,
            "board_dimension": self.board_dimension,
            "turn": self.turn,
            "path_clear": self.path_clear,
            "pieces_matching": self.pieces_matching,
            "squares_attacked": self.squares_attacked,
        }
