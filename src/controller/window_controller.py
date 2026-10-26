"""Window lifecycle and status state; no independent game or clock authority."""

from __future__ import annotations

from typing import Any

from controller.controller import GameController

GAME_LABELS = {"chess": "Chess", "checkers": "English Draughts"}


def display_game_name(game: str) -> str:
    """Keep identifiers stable while presenting a player-friendly name."""
    return GAME_LABELS.get(game, game.replace("_", " ").title())


def square_name(position: tuple[int, int], rows: int = 8) -> str:
    """A user-facing board coordinate rather than a Python tuple."""
    row, column = position
    return f"{chr(ord('a') + column)}{rows - row}"


class WindowController:
    """Own window status and route clicks to the local desktop session."""

    def __init__(
        self,
        game_controller: GameController | None = None,
        title: str = "BoardGamesWithQuests",
        dimensions: tuple[int, int] = (800, 600),
    ) -> None:
        self.game_controller = game_controller or GameController()
        self.title = title
        self.width, self.height = dimensions
        self.is_running = False
        self.status_message = "Welcome to BoardGamesWithQuests"
        self.active_dialog: str | None = None

    def game_title(self) -> str:
        return f"{self.title} - {display_game_name(self.game_controller.session.game)}"

    def start(self) -> None:
        self.is_running = True
        self.status_message = "Game started"

    def stop(self) -> None:
        self.is_running = False
        self.status_message = "Game stopped"

    def set_status(self, message: str) -> None:
        self.status_message = message

    def show_dialog(self, message: str) -> None:
        self.active_dialog = message

    def close_dialog(self) -> None:
        self.active_dialog = None

    def on_square_clicked(self, position: tuple[int, int]) -> dict[str, Any]:
        result = self.game_controller.handle_square_click(position)
        action = result["action"]
        if action == "moved":
            move = result["event"].get("move")
            if move is None:
                self.set_status("Move completed.")
            else:
                rows = result["game_state"]["config"]["board"]["rows"]
                route = [move["start"], *move["hops"]]
                self.set_status(
                    "Played "
                    + " → ".join(square_name(tuple(square), rows) for square in route)
                    + "."
                )
        elif action in ("selected", "reselected"):
            state = self.game_controller.session.snapshot()
            rows = state["config"]["board"]["rows"]
            self.set_status(f"Selected {square_name(position, rows)}. Choose a highlighted square.")
        elif action == "none":
            self.set_status("Select a piece belonging to the player to move.")
        elif action == "invalid":
            self.set_status(result.get("message", "That move is not available."))
        return result

    def tick_timer(self) -> bool:
        completed = self.game_controller.session.poll_timeout()
        if completed:
            self.set_status("Time expired.")
        return completed
