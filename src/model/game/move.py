"""Move representation tracking positions, piece transitions, captures, and promotions."""

from typing import Any, List, NamedTuple, Optional, Tuple

#: One disturbed square: where it is, what stood on it, and whether that piece had moved.
Disturbed = Tuple[Tuple[int, int], Optional[Any], bool]


def _square(position: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    """Read a coordinate pair, or nothing at all.

    Args:
        position: A (row, col) pair, or None for a move that has no such square.

    Returns:
        Optional[Tuple[int, int]]: The pair as a plain tuple, or None.
    """
    return None if position is None else (position[0], position[1])


class Applied(NamedTuple):
    """Everything a move disturbed, so that the position can be put back exactly.

    Attributes:
        squares: Every square the move wrote to, as (square, piece, had the piece moved)
            triples, in the order it touched them.
        captures: How many pieces each side had captured before the move, because a move
            that is only being looked at must not leave its capture behind on the board.
    """

    squares: List[Disturbed]
    captures: Tuple[int, int]


class Move:
    """Encapsulates a chess move with coordinates, piece states, and execution logic.

    Attributes:
        start_pos: The (row, col) square the move begins on.
        end_pos: The (row, col) square the move ends on.
        piece: The piece that moves, once one has been established.
        move_type: What kind of move this is, which is what makes it special.
        captured_piece: The piece this move took, recorded while the board still held it.
        promotion_piece: The piece that replaces the mover, when it changes kind.
        capture_from: The square a taken piece stands on when it is not the destination.
        companion_start: The square a second piece leaves, for a move that carries one along.
        companion_end: The square that second piece ends on.
    """

    #: The (row, col) square the move begins on.
    start_pos: Tuple[int, int]
    #: The (row, col) square the move ends on.
    end_pos: Tuple[int, int]
    #: The square a taken piece stands on when it is not the destination.
    capture_from: Optional[Tuple[int, int]]
    #: The square a second piece leaves, for a move that carries one along.
    companion_start: Optional[Tuple[int, int]]
    #: The square that second piece ends on.
    companion_end: Optional[Tuple[int, int]]

    def __init__(
        self,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        piece: Optional[Any] = None,
        move_type: str = "normal",
        captured_piece: Optional[Any] = None,
        promotion_piece: Optional[Any] = None,
        capture_from: Optional[Tuple[int, int]] = None,
        companion_start: Optional[Tuple[int, int]] = None,
        companion_end: Optional[Tuple[int, int]] = None,
        *,
        hops: Optional[Tuple[Tuple[int, int], ...]] = None,
        promotion: Optional[str] = None,
    ):
        """Initialize a Move instance.

        Args:
            start_pos: Starting (row, col) coordinates.
            end_pos: Destination (row, col) coordinates.
            piece: Moving piece instance, or None to infer from board.
            move_type: Type of move (e.g. "normal", "castling", "en_passant").
            captured_piece: Captured piece instance if any.
            promotion_piece: New piece instance if move involves promotion.
            capture_from: Square a captured piece stands on when it is not the destination.
                An en passant capture takes the piece that stepped past.
            companion_start: Square a second piece starts from, for a move that carries one
                along. Castling moves a rook with its king.
            companion_end: Square that second piece ends on.
        """
        self.start_pos = (start_pos[0], start_pos[1])
        self.end_pos = (end_pos[0], end_pos[1])
        self.piece = piece
        self.move_type = move_type
        self.captured_piece = captured_piece
        self.promotion_piece = promotion_piece
        self.capture_from = _square(capture_from)
        self.companion_start = _square(companion_start)
        self.companion_end = _square(companion_end)
        self.hops = tuple((row, col) for row, col in hops) if hops is not None else (self.end_pos,)
        self.promotion = promotion

    @classmethod
    def from_json(cls, data: Any) -> "Move":
        """Parse an exact, bounded declarative action intent from inert JSON."""
        if not isinstance(data, dict) or set(data) != {"start", "hops", "promotion"}:
            raise ValueError("move intent requires exactly start, hops and promotion")

        def square(value: Any) -> Tuple[int, int]:
            if (
                not isinstance(value, list)
                or len(value) != 2
                or any(type(axis) is not int or not 0 <= axis <= 255 for axis in value)
            ):
                raise ValueError("a move square must be a bounded JSON integer pair")
            return (value[0], value[1])

        start = square(data["start"])
        hops = data["hops"]
        if not isinstance(hops, list) or not 1 <= len(hops) <= 128:
            raise ValueError("move intent requires one to 128 landing squares")
        landings = tuple(square(hop) for hop in hops)
        if start == landings[0]:
            raise ValueError("the first landing must differ from the source")
        promotion = data["promotion"]
        if promotion is not None and (
            not isinstance(promotion, str) or not promotion or len(promotion) > 128
        ):
            raise ValueError("promotion must name one bounded configured piece kind")
        return cls(start, landings[-1], hops=landings, promotion=promotion)

    def to_json(self) -> dict[str, Any]:
        """Serialize only a game action intent; never include mutable piece objects."""
        return {
            "start": list(self.start_pos),
            "hops": [list(square) for square in self.hops],
            "promotion": self.promotion,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Move):
            return NotImplemented
        return (
            self.start_pos == other.start_pos
            and self.hops == other.hops
            and self.promotion == other.promotion
        )

    def __hash__(self) -> int:
        return hash((self.start_pos, self.hops, self.promotion))

    @staticmethod
    def _bounds(board: Optional[Any]) -> Tuple[int, int]:
        """Return the (rows, cols) a move is measured against.

        Args:
            board: The board the move is played on, or None to use `Board`'s default size.

        Returns:
            Tuple[int, int]: The board dimensions the move must fit inside.
        """
        if board is not None:
            return board.rows, board.cols
        from model.game.board import Board

        return Board.DEFAULT_DIMENSIONS

    def validate(self, board: Optional[Any] = None) -> bool:
        """Validate geometric boundaries and basic board rules for this move.

        Args:
            board: Optional Board instance to verify piece existence and target color. Its
                dimensions decide what is in bounds, so a move may be validated on a board
                of any size.

        Returns:
            True if basic validity checks pass, False otherwise.
        """
        rows, cols = self._bounds(board)
        if not (0 <= self.start_pos[0] < rows and 0 <= self.start_pos[1] < cols):
            return False
        if not (0 <= self.end_pos[0] < rows and 0 <= self.end_pos[1] < cols):
            return False
        if self.start_pos == self.end_pos:
            return False
        if board is not None:
            moving = board.get_piece_at(self.start_pos)
            if moving is None:
                return False
            target = board.get_piece_at(self.end_pos)
            if target is not None and target.getColor() == moving.getColor():
                return False
        return True

    def apply_to_board(self, board: Any) -> Optional[Applied]:
        """Put this move on the board and report everything needed to take it off again.

        One pair does the work for both callers, and that is the point of it. Playing a move
        and asking whether a move would be legal have to see the same position afterwards,
        so the rook that castling carries is carried here too and the piece an en passant
        capture takes is lifted here too. A legality test that only swapped the two squares
        it named saw a position with one blocker fewer than reality, and every pin through
        that blocker was invisible.

        Args:
            board: The board the move is played on.

        Returns:
            Optional[Applied]: What the move disturbed, or None when it could not be applied
            at all because nothing stands on its starting square.
        """
        piece = self.piece if self.piece is not None else board.get_piece_at(self.start_pos)
        if piece is None:
            return None
        self.piece = piece

        applied = Applied(
            squares=self._disturbed(board),
            captures=(len(board.captured_white), len(board.captured_black)),
        )

        if self.capture_from is not None:
            self.captured_piece = board.get_piece_at(self.capture_from)
            board.set_piece_at(self.capture_from, None)
            # The taken piece is not necessarily on the move destination.
            # Record it exactly once: move_piece() sees no target here.
            if self.captured_piece is not None:
                taken_color = self.captured_piece.getColor()
                if taken_color in (1, "white"):
                    board.captured_white.append(self.captured_piece)
                else:
                    board.captured_black.append(self.captured_piece)
        else:
            self.captured_piece = board.get_piece_at(self.end_pos)

        if not board.move_piece(self.start_pos, self.end_pos):
            self.unapply_from_board(board, applied)
            self.captured_piece = None
            return None

        if self.companion_start is not None and self.companion_end is not None:
            companion = board.get_piece_at(self.companion_start)
            board.set_piece_at(self.companion_start, None)
            if companion is not None:
                board.set_piece_at(self.companion_end, companion)

        if self.promotion_piece is not None:
            board.replace_piece(self.end_pos, self.promotion_piece)
        return applied

    def unapply_from_board(self, board: Any, applied: Optional[Applied]) -> None:
        """Put back everything `apply_to_board` took off the board.

        Each disturbed square gets its own occupant back, and each piece gets its moved flag
        back, because that flag is what says a piece has spent its one-off first advance and
        what says a rook has already left its home square. A legality test that left the
        flag set spent both.

        Args:
            board: The board the move was applied to.
            applied: What `apply_to_board` reported. None is accepted and does nothing.

        Returns:
            None
        """
        if applied is None:
            return
        for square, occupant, has_moved in reversed(applied.squares):
            board.set_piece_at(square, occupant)
            if occupant is not None:
                occupant.has_moved = has_moved
        del board.captured_white[applied.captures[0] :]
        del board.captured_black[applied.captures[1] :]

    def execute(self, board: Any) -> bool:
        """Execute this move on the given board.

        Args:
            board: Board instance on which the move is applied.

        Returns:
            True if the move executed successfully, False otherwise.
        """
        return self.apply_to_board(board) is not None

    def _disturbed(self, board: Any) -> List[Disturbed]:
        """List every square this move is about to write to, and what is on it now.

        Args:
            board: The board the move would be played on.

        Returns:
            List[Disturbed]: One entry per square, the starting and ending squares first
            and the two companion squares last, each recording the piece that stood there
            and whether that piece had already moved.
        """
        squares: List[Tuple[int, int]] = [self.start_pos, self.end_pos]
        if self.capture_from is not None:
            squares.append(self.capture_from)
        for square in (self.companion_start, self.companion_end):
            if square is not None:
                squares.append(square)

        disturbed: List[Disturbed] = []
        for square in squares:
            if any(recorded[0] == square for recorded in disturbed):
                continue
            occupant = board.get_piece_at(square)
            disturbed.append((square, occupant, occupant.has_moved if occupant else False))
        return disturbed


#: Czech alias for `Move`, as `PRD.md` section 5 and `Tah` in the diagram require.
Tah = Move
