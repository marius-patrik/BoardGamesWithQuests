"""Generic bounded board geometry used by declarative JSON rules."""

from __future__ import annotations

from model.game.board import Board
from model.pieces.piece import Piece


class MoveValidator:
    """Read-only movement/attack geometry; never loads executable variant rules."""

    def __init__(self, board: Board | None = None) -> None:
        self.board = board

    @staticmethod
    def _step_limit(piece: Piece, board: Board) -> int:
        if piece.canJump():
            return 1
        maximum = piece.getMaxSteps()
        return (
            max(1, min(maximum, max(board.rows, board.cols)))
            if maximum
            else max(board.rows, board.cols)
        )

    @staticmethod
    def _ray(
        board: Board,
        source: tuple[int, int],
        row_delta: int,
        col_delta: int,
        steps: int,
        *,
        can_jump: bool = False,
    ):
        for distance in range(1, steps + 1):
            target = (source[0] + row_delta * distance, source[1] + col_delta * distance)
            if not board.is_within_bounds(*target):
                break
            yield target
            if not can_jump and board.get_piece_at(target) is not None:
                break

    def get_geometric_moves(
        self, start_pos: tuple[int, int], board: Board | None = None
    ) -> list[tuple[int, int]]:
        """Enumerate declarative piece geometry, not final game-law legality."""
        position = board if board is not None else self.board
        if position is None or not position.is_within_bounds(*start_pos):
            return []
        piece = position.get_piece_at(start_pos)
        if piece is None:
            return []
        quiet = piece.getDirections() or []
        attacks = piece.getAttackDirections() or []
        limit = self._step_limit(piece, position)
        candidates: list[tuple[int, int]] = []
        seen: set[tuple[int, int]] = set()

        def admit(target: tuple[int, int], *, quiet_allowed: bool, capture_allowed: bool):
            occupant = position.get_piece_at(target)
            if occupant is not None and (
                not capture_allowed or occupant.getColor() == piece.getColor()
            ):
                return
            if occupant is None and not quiet_allowed:
                return
            if target not in seen:
                seen.add(target)
                candidates.append(target)

        for direction in quiet:
            if direction in attacks:
                for target in self._ray(
                    position,
                    start_pos,
                    direction[0],
                    direction[1],
                    limit,
                    can_jump=piece.canJump(),
                ):
                    admit(target, quiet_allowed=True, capture_allowed=True)
            else:
                for target in self._ray(
                    position,
                    start_pos,
                    direction[0],
                    direction[1],
                    limit,
                    can_jump=piece.canJump(),
                ):
                    if position.get_piece_at(target) is not None:
                        break
                    admit(target, quiet_allowed=True, capture_allowed=False)
        for direction in attacks:
            if direction in quiet:
                continue
            for target in self._ray(
                position,
                start_pos,
                direction[0],
                direction[1],
                limit,
                can_jump=piece.canJump(),
            ):
                admit(target, quiet_allowed=False, capture_allowed=True)
        if not piece.hasMoved():
            for dr, dc in piece.getInitialVectors():
                target = (start_pos[0] + dr, start_pos[1] + dc)
                if not position.is_within_bounds(*target):
                    continue
                if position.get_piece_at(target) is not None:
                    continue
                steps = max(abs(dr), abs(dc))
                if steps == 0:
                    continue
                if any(
                    position.get_piece_at(
                        (start_pos[0] + (dr // steps) * index, start_pos[1] + (dc // steps) * index)
                    )
                    is not None
                    for index in range(1, steps)
                ):
                    continue
                admit(target, quiet_allowed=True, capture_allowed=False)
        return candidates

    def is_square_attacked(
        self,
        target_square: tuple[int, int],
        by_color: int,
        board: Board | None = None,
    ) -> bool:
        """True for geometrically attacked squares, including king-protected squares."""
        position = board if board is not None else self.board
        if position is None or not position.is_within_bounds(*target_square):
            return False
        if type(by_color) is not int or by_color not in (-1, 1):
            raise ValueError("attacking side must be -1 or 1")
        for row in range(position.rows):
            for col in range(position.cols):
                piece = position.get_piece_at((row, col))
                if piece is None or piece.getColor() != by_color:
                    continue
                for dr, dc in piece.getAttackDirections() or []:
                    for target in self._ray(
                        position,
                        (row, col),
                        dr,
                        dc,
                        self._step_limit(piece, position),
                        can_jump=piece.canJump(),
                    ):
                        if target == target_square:
                            return True
        return False
