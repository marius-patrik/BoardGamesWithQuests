"""Window lifecycle and status state; no independent game or clock authority."""

from __future__ import annotations

from typing import Any

from controller.controller import GameController


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
        if result["action"] == "moved":
            self.set_status("Move played.")
        elif result["action"] in ("selected", "reselected"):
            self.set_status(f"Selected {position}")
        elif result["action"] == "invalid":
            self.set_status(result.get("message", "Invalid move."))
        return result

    def tick_timer(self) -> bool:
        completed = self.game_controller.session.poll_timeout()
        if completed:
            self.set_status("Time expired.")
        return completed
