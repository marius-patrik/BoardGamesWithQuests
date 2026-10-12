"""Generic movement geometry and optional royal-safety primitives.

A candidate is not a game-legal move until all game-specific rules permit it.
In particular, castling, en-passant, mandatory captures and multi-jumps are
rules supplied by game packages, not special cases inferred from piece names.
"""

from typing import List, Optional, Tuple

from engine.model.game.board import Board
from engine.model.game.move import Move
from engine.model.pieces.piece import Piece

Square = Tuple[int, int]


class MoveValidator:
    """Generate geometric candidates without depending on any named game or piece.

    The optional royal-safety filter is driven by the piece's `isRoyal()`
    capability. This class does not claim game-specific move completeness.
    """

    def __init__(self, board: Optional[Board] = None, move: Optional[Move] = None):
        """Initialize the geometric validator.

        Args:
            board: Board supplying dimensions and occupancy.
            move: Optional move to inspect.
        """
        self.board = board
        self.move = move

    def set_board(self, board: Board) -> None:
        """Set the board used by default."""
        self.board = board

    def set_move(self, move: Move) -> None:
        """Set the current move used by callers."""
        self.move = move

    @staticmethod
    def _limit(piece: Piece, board: Board) -> int:
        """Derive the maximum ray length from capabilities and board geometry."""
        return max(board.rows, board.cols) - 1 if piece.canRepeat() else 1

    @staticmethod
    def _walk(board: Board, origin: Square, vector: Square, limit: int):
        """Yield in-bounds destinations along a vector, stopping at occupied squares."""
        if vector == (0, 0):
            return
        dr, dc = vector
        for step in range(1, limit + 1):
            pos = (origin[0] + dr * step, origin[1] + dc * step)
            if not board.is_within_bounds(*pos):
                break
            yield pos
            if board.get_piece_at(pos) is not None:
                break

    def find_royal(self, color: int, board: Optional[Board] = None) -> Optional[Square]:
        """Find a royal piece declared by the game for the given side."""
        b = board or self.board
        if b is None:
            return None
        for row in range(b.rows):
            for col in range(b.cols):
                piece = b.get_piece_at((row, col))
                if piece is not None and piece.getColor() == color and piece.isRoyal():
                    return row, col
        return None

    def is_square_attacked(
        self, target_square: Square, by_color: int, board: Optional[Board] = None
    ) -> bool:
        """Report whether a side geometrically attacks an in-bounds square."""
        b = board or self.board
        if b is None or not b.is_within_bounds(*target_square):
            return False
        for row in range(b.rows):
            for col in range(b.cols):
                piece = b.get_piece_at((row, col))
                if piece is None or piece.getColor() != by_color:
                    continue
                for vector in piece.getAttackDirections():
                    for pos in self._walk(b, (row, col), vector, self._limit(piece, b)):
                        if pos == target_square:
                            return True
        return False

    def is_check(self, color: int, board: Optional[Board] = None) -> bool:
        """Check configured royal safety for one side; no royal means no check."""
        b = board or self.board
        royal = self.find_royal(color, b)
        if royal is None:
            return False
        return self.is_square_attacked(royal, -color, b)

    @staticmethod
    def _initial_path_clear(board: Board, origin: Square, offset: Square) -> bool:
        """Check an initial multi-square quiet move does not cross occupied squares.

        Nonlinear offsets that cannot be traced in a straight line are rejected
        unless the piece explicitly declares itself a jumper.
        """
        import math

        dr, dc = offset
        count = math.gcd(abs(dr), abs(dc))
        if count == 0:
            return False
        step = (dr // count, dc // count)
        for distance in range(1, count + 1):
            pos = (origin[0] + step[0] * distance, origin[1] + step[1] * distance)
            if not board.is_within_bounds(*pos) or board.get_piece_at(pos) is not None:
                return False
        return True

    def get_pseudo_legal_moves(
        self, start_pos: Square, board: Optional[Board] = None
    ) -> List[Square]:
        """Find destinations consistent with movement and occupancy capabilities.

        This does not apply special rules or game-specific win conditions.
        """
        b = board or self.board
        if b is None:
            return []
        piece = b.get_piece_at(start_pos)
        if piece is None:
            return []

        quiet = set(piece.getDirections())
        attacks = set(piece.getAttackDirections())
        seen: set[Square] = set()
        destinations: List[Square] = []
        for vector in piece.getDirections() + piece.getAttackDirections():
            if vector == (0, 0):
                continue
            if vector not in quiet and vector not in attacks:
                continue
            for dest in self._walk(b, start_pos, vector, self._limit(piece, b)):
                target = b.get_piece_at(dest)
                allowed = (
                    (target is None and vector in quiet)
                    or (target is not None and target.getColor() != piece.getColor() and vector in attacks)
                )
                if allowed and dest not in seen:
                    seen.add(dest)
                    destinations.append(dest)
                if target is not None:
                    break

        if not piece.hasMoved():
            for vector in piece.getInitialVectors():
                dest = (start_pos[0] + vector[0], start_pos[1] + vector[1])
                if (
                    b.is_within_bounds(*dest)
                    and dest not in seen
                    and (
                        piece.canJump() and b.get_piece_at(dest) is None
                        or not piece.canJump() and self._initial_path_clear(b, start_pos, vector)
                    )
                ):
                    seen.add(dest)
                    destinations.append(dest)
        return destinations

    def get_valid_moves(
        self, start_pos: Square, board: Optional[Board] = None
    ) -> List[Square]:
        """Filter geometric candidates through configured royal safety only.

        Full game legality requires additional rule evaluation, which the
        incomplete game packages do not expose yet.
        """
        b = board or self.board
        if b is None:
            return []
        piece = b.get_piece_at(start_pos)
        if piece is None:
            return []
        possible = self.get_pseudo_legal_moves(start_pos, b)
        legal: List[Square] = []
        for destination in possible:
            captured = b.get_piece_at(destination)
            b.set_piece_at(destination, piece)
            b.set_piece_at(start_pos, None)
            try:
                safe = not self.is_check(piece.getColor(), b)
            finally:
                b.set_piece_at(start_pos, piece)
                b.set_piece_at(destination, captured)
            if safe:
                legal.append(destination)
        return legal

    def get_all_valid_moves(self, color: int, board: Optional[Board] = None) -> List[Move]:
        """Return geometrically and royal-safe candidate moves for the given side."""
        b = board or self.board
        if b is None:
            return []
        result: List[Move] = []
        for row in range(b.rows):
            for col in range(b.cols):
                piece = b.get_piece_at((row, col))
                if piece is None or piece.getColor() != color:
                    continue
                for dest in self.get_valid_moves((row, col), b):
                    result.append(
                        Move(
                            (row, col),
                            dest,
                            piece=piece,
                            move_type="capture" if b.get_piece_at(dest) is not None else "normal",
                        )
                    )
        return result

    def is_valid_move(self, move: Move, board: Optional[Board] = None) -> bool:
        """Validate geometric and royal-safe candidacy, not full game legality."""
        b = board or self.board
        return bool(
            b is not None
            and move.validate(b)
            and move.end_pos in self.get_valid_moves(move.start_pos, b)
        )

    def is_checkmate(self, color: int, board: Optional[Board] = None) -> bool:
        """Return whether the declared royal has no basic response while attacked.

        This is a geometric diagnostic, not a final game outcome adjudication.
        """
        b = board or self.board
        return bool(b is not None and self.is_check(color, b) and not self.get_all_valid_moves(color, b))

    def is_stalemate(self, color: int, board: Optional[Board] = None) -> bool:
        """Return whether a declared royal has no basic moves and is not attacked.

        Only a game's rules can declare an actual stalemate outcome.
        """
        b = board or self.board
        return bool(
            b is not None
            and self.find_royal(color, b) is not None
            and not self.is_check(color, b)
            and not self.get_all_valid_moves(color, b)
        )
