"""Translate Tkinter square selections to canonical desktop-session intents."""

from __future__ import annotations

from typing import Any

from model.game.manager import TransitionError
from model.game.session import DesktopSession

Square = tuple[int, int]


class GameController:
    """Interpret player clicks without holding an independent game state."""

    def __init__(self, session: DesktopSession | None = None):
        self.session = session if session is not None else DesktopSession()
        self.selected_square: Square | None = None
        self.highlighted_moves: list[Square] = []

    def select_square(self, pos: Square) -> list[Square]:
        state = self.session.snapshot()
        active = state["active_side"]
        record = next((piece for piece in state["board"] if piece["square"] == list(pos)), None)
        if record is None or record["side"] != active:
            self.reset_selection()
            return []
        actions = [
            action for action in self.session.legal_actions() if action["start"] == list(pos)
        ]
        self.selected_square = pos if actions else None
        self.highlighted_moves = sorted({tuple(action["hops"][-1]) for action in actions})
        return list(self.highlighted_moves)

    def handle_square_click(self, pos: Square) -> dict[str, Any]:
        state = self.session.snapshot()
        if state["outcome"] is not None:
            return {"action": "invalid", "message": "The game has ended.", "game_state": state}
        if self.selected_square is None:
            targets = self.select_square(pos)
            return {
                "action": "selected" if targets else "none",
                "selected": self.selected_square,
                "valid_moves": targets,
            }
        record = next((piece for piece in state["board"] if piece["square"] == list(pos)), None)
        if record is not None and record["side"] == state["active_side"]:
            targets = self.select_square(pos)
            return {
                "action": "reselected",
                "selected": self.selected_square,
                "valid_moves": targets,
            }
        options = [
            move
            for move in self.session.legal_actions()
            if move["start"] == list(self.selected_square) and move["hops"][-1] == list(pos)
        ]
        if not options:
            self.reset_selection()
            return {
                "action": "invalid",
                "message": "That is not a legal destination.",
                "game_state": state,
            }
        if len(options) > 1:
            return {
                "action": "choose",
                "options": options,
                "selected": self.selected_square,
                "valid_moves": self.highlighted_moves,
            }
        return self.submit_move(options[0])

    def submit_move(self, move: dict[str, Any]) -> dict[str, Any]:
        state = self.session.snapshot()
        actor = state["participants"][str(state["active_side"])]
        try:
            result = self.session.submit(actor, state["revision"], {"type": "move", "move": move})
        except (TransitionError, ValueError) as exc:
            self.reset_selection()
            return {"action": "invalid", "message": str(exc), "game_state": self.session.snapshot()}
        self.reset_selection()
        return {
            "action": "moved",
            "success": True,
            "game_state": result["state"],
            "event": result["event"],
        }

    def reset_selection(self) -> None:
        self.selected_square = None
        self.highlighted_moves = []

    def new_game(self, game: str | None = None) -> dict[str, Any]:
        result = self.session.reset(game)
        self.reset_selection()
        return result
