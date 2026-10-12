"""Rectangular board storage, piece placement, and capture bookkeeping."""

from typing import Iterable, List, Optional, Tuple

from engine.model.pieces.piece import Piece


class Board:
    """A rectangular playing surface that tracks piece positions and captures.

    Game-specific placements and movement rules do not belong to board storage.
    A board begins empty unless its creator provides an explicit placement.
    `DEFAULT_DIMENSIONS` is a convenience only, not a game constraint.
    """

    #: Default size for callers that do not provide a game configuration.
    DEFAULT_DIMENSIONS: Tuple[int, int] = (8, 8)

    def __init__(
        self,
        dimensions: Tuple[int, int] = DEFAULT_DIMENSIONS,
        placement: Optional[Iterable[Tuple[Tuple[int, int], Piece]]] = None,
    ):
        """Initialize a board.

        Args:
            dimensions: Board dimensions as a (rows, cols) tuple.
            placement: Optional (position, piece) pairs supplied by a game configuration.

        Raises:
            ValueError: If dimensions or placement are invalid.
        """
        if (
            not isinstance(dimensions, tuple)
            or len(dimensions) != 2
            or any(type(size) is not int or size <= 0 for size in dimensions)
        ):
            raise ValueError("board dimensions must be a pair of positive integers (rows, cols)")

        self.dimensions = dimensions
        self.rows, self.cols = dimensions
        self.board: List[List[Optional[Piece]]] = [
            [None for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self.captured_white: List[Piece] = []
        self.captured_black: List[Piece] = []

        if placement is not None:
            self.apply_placement(placement)

    def is_within_bounds(self, row: int, col: int) -> bool:
        """Check if coordinates lie within the board boundaries.

        Args:
            row: 0-indexed board row.
            col: 0-indexed board column.

        Returns:
            True if (row, col) is within bounds, False otherwise.
        """
        return (
            type(row) is int and type(col) is int and 0 <= row < self.rows and 0 <= col < self.cols
        )

    def get_piece_at(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Retrieve the piece located at the specified board position.

        Args:
            position: Tuple of (row, col) coordinates.

        Returns:
            Piece instance at the position, or None if empty or out of bounds.
        """
        row, col = position
        if not self.is_within_bounds(row, col):
            return None
        return self.board[row][col]

    def set_piece_at(self, position: Tuple[int, int], piece: Optional[Piece]) -> None:
        """Place or remove a piece at a specified position.

        Args:
            position: Tuple of (row, col) coordinates.
            piece: Piece instance to place, or None to clear square.
        """
        row, col = position
        if not self.is_within_bounds(row, col):
            raise IndexError(f"square {position!r} is outside {self.rows}x{self.cols} board")
        self.board[row][col] = piece

    def move_piece(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> bool:
        """Move a piece from start_pos to end_pos, tracking captured pieces.

        Args:
            start_pos: Source (row, col) coordinates.
            end_pos: Target (row, col) coordinates.

        Returns:
            True if the piece was successfully moved, False if invalid or empty start.
        """
        if start_pos == end_pos:
            return False
        piece = self.get_piece_at(start_pos)
        if piece is None or not self.is_within_bounds(*end_pos):
            return False

        target = self.get_piece_at(end_pos)
        if target is not None and target.getColor() == piece.getColor():
            return False
        if target is not None:
            if target.getColor() == 1 or target.getColor() == "white":
                self.captured_white.append(target)
            else:
                self.captured_black.append(target)

        self.set_piece_at(end_pos, piece)
        self.set_piece_at(start_pos, None)
        if hasattr(piece, "setMoved"):
            piece.setMoved(True)
        return True

    def replace_piece(self, position: Tuple[int, int], new_piece: Piece) -> None:
        """Replace a piece at the given position (e.g. during pawn promotion).

        Args:
            position: Target (row, col) coordinate.
            new_piece: Replacement Piece instance.
        """
        self.set_piece_at(position, new_piece)

    def apply_placement(self, placement: Iterable[Tuple[Tuple[int, int], Piece]]) -> None:
        """Replace the board position atomically with an explicit placement.

        A malformed placement leaves the current board and capture history untouched.

        Args:
            placement: (position, piece) pairs with distinct in-bounds squares.

        Raises:
            ValueError: If a square is out of bounds, repeated, or has no piece.
        """
        new_board: List[List[Optional[Piece]]] = [
            [None for _ in range(self.cols)] for _ in range(self.rows)
        ]
        occupied: set[Tuple[int, int]] = set()
        for position, piece in placement:
            row, col = position
            if not self.is_within_bounds(row, col):
                raise ValueError(f"placement square {position!r} is out of bounds")
            if (row, col) in occupied:
                raise ValueError(f"duplicate placement square {position!r}")
            if piece is None:
                raise ValueError(f"placement square {position!r} has no piece")
            occupied.add((row, col))
            new_board[row][col] = piece

        self.board = new_board
        self.captured_white.clear()
        self.captured_black.clear()

