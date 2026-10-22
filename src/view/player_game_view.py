"""Tkinter gameplay sourced exclusively from detached JSON session snapshots."""

from __future__ import annotations

import json
from model.game.persistence import SessionFileError, load_session, save_session
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

from controller.window_controller import WindowController
from model.game.preferences import DEFAULTS, PreferencesError, load_preferences
from view.game_view import BoardView
from view.player_view import PlayerView
from view.quest_view import QuestList

REFRESH_INTERVAL_MS = 500


class PlayerGameView(ttk.Frame):
    """Game board, participants, quests and move history; no independent authority."""

    def __init__(
        self,
        master: tk.Misc,
        window_controller: WindowController,
        square_size: int = 56,
        on_settings=None,
        on_new_game_request=None,
    ) -> None:
        super().__init__(master, padding=10)
        self.window_controller = window_controller
        self.on_settings = on_settings
        self.on_new_game_request = on_new_game_request
        self.turn = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self._timer_id: str | None = None
        self._last_history: tuple[Any, ...] | None = None
        self._build_layout(square_size)
        self.refresh()

    @property
    def session(self):
        return self.window_controller.game_controller.session

    def _build_layout(self, square_size: int) -> None:
        heading = ttk.Frame(self)
        heading.pack(fill="x")
        ttk.Label(heading, text="BoardGamesWithQuests", font=("TkDefaultFont", 16, "bold")).pack(
            side="left"
        )
        ttk.Button(heading, text="New game", command=self.on_new_game).pack(side="right")
        if self.on_settings is not None:
            ttk.Button(heading, text="Settings", command=self.on_settings).pack(
                side="right", padx=(0, 6)
            )
        ttk.Button(heading, text="Open game", command=self.open_game).pack(
            side="right", padx=(0, 6)
        )
        ttk.Button(heading, text="Export", command=self.export_game).pack(side="right", padx=(0, 6))
        ttk.Button(heading, text="Quit", command=self._quit).pack(side="right", padx=(0, 6))

        self.top_player = PlayerView(self, -1)
        self.top_player.pack(fill="x")
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, textvariable=self.turn, font=("TkDefaultFont", 12)).pack(anchor="w")
        try:
            config = load_preferences()
        except PreferencesError:
            config = dict(DEFAULTS)
        self.board_view = BoardView(
            left,
            self.session.board_projection(),
            on_square_clicked=self.on_square_clicked,
            square_size=config["board_size"],
            show_coordinates=config["show_coordinates"],
        )
        self.board_view.pack(pady=6)
        self.bottom_player = PlayerView(left, 1)
        self.bottom_player.pack(fill="x")

        right = ttk.Frame(body, padding=(12, 0))
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Quests", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        self.quest_list = QuestList(right)
        self.quest_list.pack(fill="both", expand=True)
        ttk.Label(right, text="Moves", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        self.history = tk.Listbox(right, height=10, width=28)
        self.history.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(
            fill="x", pady=(8, 0)
        )

    def on_square_clicked(self, position: tuple[int, int]) -> None:
        result = self.window_controller.on_square_clicked(position)
        if result["action"] == "choose":
            options = result["options"]
            descriptions = [
                f"{index + 1}. {move['hops']} {move['promotion'] or ''}"
                for index, move in enumerate(options)
            ]
            choice = simpledialog.askinteger(
                "Choose move",
                "Select a complete capture route or promotion:\n" + "\n".join(descriptions),
                parent=self,
                minvalue=1,
                maxvalue=len(options),
            )
            if choice is not None:
                result = self.window_controller.game_controller.submit_move(options[choice - 1])
                if result["action"] == "moved":
                    self.window_controller.set_status("Move played.")
        controller = self.window_controller.game_controller
        self.board_view.set_selection(controller.selected_square, controller.highlighted_moves)
        if result["action"] == "invalid":
            self.status.set(result.get("message", "Invalid move."))
        self.refresh()

    def reload(self) -> None:
        """Redraw after a real game switch or session reset."""
        self.window_controller.game_controller.reset_selection()
        self._last_history = None
        self.board_view.set_selection(None, [])
        self.refresh()

    def on_new_game(self) -> None:
        if self.on_new_game_request is not None:
            self.on_new_game_request()
            return
        self.window_controller.game_controller.new_game()
        self.reload()

    @staticmethod
    def _label(square: list[int], rows: int) -> str:
        return f"{chr(ord('a') + square[1])}{rows - square[0]}"

    def refresh(self) -> None:
        state = self.session.snapshot()
        self.board_view.refresh(self.session.board_projection())
        remaining = self.session.clock_remaining()
        self.top_player.refresh(state, remaining)
        self.bottom_player.refresh(state, remaining)
        active = "White" if state["active_side"] == 1 else "Black"
        self.turn.set(f"{self.session.game} · {active} to move · turn {state['revision'] + 1}")
        self.quest_list.refresh(state)
        if state["outcome"] is not None:
            self.status.set(f"Game ended: {state['outcome']['kind']}")
        elif self.window_controller.status_message:
            self.status.set(self.window_controller.status_message)

        events = tuple(json.dumps(entry, sort_keys=True) for entry in state["events"])
        if events != self._last_history:
            self._last_history = events
            self.history.delete(0, tk.END)
            for event in state["events"]:
                move = event.get("move")
                if move is None:
                    description = event.get("action", {}).get("type", "Result")
                else:
                    description = (
                        self._label(move["start"], state["config"]["board"]["rows"])
                        + " → "
                        + " → ".join(
                            self._label(square, state["config"]["board"]["rows"])
                            for square in move["hops"]
                        )
                    )
                    if move.get("promotion"):
                        description += f"={move['promotion']}"
                self.history.insert(tk.END, f"{event['revision']}. {description}")
            self.history.yview_moveto(1.0)

    def apply_preferences(self, values: dict[str, Any]) -> None:
        self.board_view.square_size = values["board_size"]
        self.board_view.show_coordinates = values["show_coordinates"]
        self.board_view.refresh()

    def open_game(self) -> None:
        source = filedialog.askopenfilename(
            parent=self, filetypes=[("Saved games", "*.json")]
        )
        if not source:
            return
        try:
            restored = load_session(source)
        except (OSError, SessionFileError, ValueError, TypeError) as error:
            messagebox.showerror("Open game", str(error), parent=self)
            return
        self.window_controller.game_controller.session = restored
        self.reload()
        self.status.set(f"Restored {restored.game}.")

    def export_game(self) -> None:
        destination = filedialog.asksaveasfilename(
            parent=self, defaultextension=".json", filetypes=[("Saved games", "*.json")]
        )
        if not destination:
            return
        try:
            save_session(self.session, destination)
        except (OSError, SessionFileError, ValueError) as error:
            messagebox.showerror("Export", str(error), parent=self)
            return
        self.status.set(f"Exported game to {destination}")

    def _quit(self) -> None:
        self.stop_auto_refresh()
        self.window_controller.stop()
        self.winfo_toplevel().destroy()

    def stop_auto_refresh(self) -> None:
        if self._timer_id is not None:
            try:
                self.after_cancel(self._timer_id)
            except tk.TclError:
                pass
            self._timer_id = None

    def start_auto_refresh(self, interval_ms: int = REFRESH_INTERVAL_MS):
        self.stop_auto_refresh()
        self._timer_interval = interval_ms
        self._timer_id = self.after(interval_ms, self._auto_refresh)
        return self._timer_id

    def _auto_refresh(self) -> None:
        self._timer_id = None
        try:
            if not self.winfo_exists() or not self.window_controller.is_running:
                return
            self.window_controller.tick_timer()
            self.refresh()
            self._timer_id = self.after(self._timer_interval, self._auto_refresh)
        except tk.TclError:
            self._timer_id = None

    def destroy(self) -> None:
        self.stop_auto_refresh()
        super().destroy()
