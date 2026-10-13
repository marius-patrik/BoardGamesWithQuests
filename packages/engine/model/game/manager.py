"""Game manager coordinating board state, turn alternation, clock ticks, and game rules."""

from typing import List, Optional, Any

try:
    from engine.model.game.board import Board
    from engine.model.game.move import Move
    from engine.model.game.player import Player
    from engine.model.game.timer import Timer
    from engine.model.game.logger import GameLogger
    from engine.model.game.validator import MoveValidator
except ImportError:
    from .board import Board
    from .move import Move
    from .player import Player
    from .timer import Timer
    from .logger import GameLogger
    from .validator import MoveValidator


class GameManager:
    """Core game orchestrator managing turns, clocks, moves, and terminal game conditions."""

    def __init__(
        self,
        board: Board,
        players: List[Player],
        timer: Timer,
        logger: Optional[GameLogger] = None,
        validator: Optional[MoveValidator] = None,
    ):
        """Create a session with explicit board, two players and clock.

        The active game configuration must be supplied by the caller; implicit
        chess-specific board, timer and participant defaults are prohibited.
        """
        if board is None or timer is None or players is None or len(players) != 2:
            raise ValueError("board, clock and exactly two players are required")
        if players[0].getColor() == players[1].getColor():
            raise ValueError("players must control distinct sides")
        self.board = board
        self.players = list(players)
        self.active_player = self.players[0].getColor()
        self.current_move: Optional[Move] = None
        self.timer = timer
        self.game_logger = logger if logger is not None else GameLogger()
        self.move_validator = validator if validator is not None else MoveValidator(board)

    def start_turn(self) -> Optional[Move]:
        """Begin a new turn, clearing any pending move selection.

        Returns:
            Always None indicating no pending move.
        """
        self.current_move = None
        return self.current_move

    def get_valid_moves(self) -> List[Move]:
        """Compute all legal moves available to the active player.

        Returns:
            List of legal Move instances for the active player.
        """
        return self.move_validator.get_all_valid_moves(self.active_player, self.board)

    possible_moves = get_valid_moves

    def cancel_move(self) -> None:
        """Cancel or reset the currently selected move."""
        self.current_move = None

    def save_log(self) -> None:
        """Save the game log (stub implementation)."""
        pass

    def get_state(self) -> Any:
        """Fail closed until JSON-configured outcome evaluation is integrated."""
        raise NotImplementedError("game result requires configured outcome hooks")

    def make_move(self, move: Move) -> bool:
        """Validate and execute a move, log it, and switch the active player.

        Args:
            move: Move instance to execute.

        Returns:
            True if the move was valid and successfully executed, False otherwise.
        """
        if not self.move_validator.is_valid_move(move, self.board):
            return False
        piece = self.board.get_piece_at(move.start_pos)
        if piece is None or piece.getColor() != self.active_player:
            return False

        success = move._apply_validated(self.board)
        if not success:
            return False

        self.current_move = move
        self.game_logger.log_move(move)
        self.active_player = -1 if self.active_player == 1 else 1
        return True
