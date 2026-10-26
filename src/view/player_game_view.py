"""Tkinter gameplay sourced exclusively from detached JSON session snapshots."""

from __future__ import annotations

import json
from model.game.persistence import SessionFileError, load_session, save_session
from model.game.notation import NotationError, save_notation
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
        # The original single-row right-packed toolbar clipped its leftmost
        # controls. Two grouped rows remain reachable even at 840 px.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        heading = ttk.Frame(self)
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="BoardGamesWithQuests", font=("TkDefaultFont", 16, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        navigation = ttk.Frame(heading)
        navigation.grid(row=0, column=1, sticky="e")
        gameplay = ttk.Frame(heading)
        gameplay.grid(row=1, column=0, columnspan=2, sticky="e", pady=(4, 0))
        self.action_buttons: dict[str, ttk.Button] = {}

        def add_action(group: ttk.Frame, label: str, command) -> None:
            button = ttk.Button(group, text=label, command=command)
            button.pack(side="left", padx=(4, 0))
            self.action_buttons[label] = button

        add_action(navigation, "New game", self.on_new_game)
        add_action(navigation, "Open game", self.open_game)
        if self.on_settings is not None:
            add_action(navigation, "Settings", self.on_settings)
        add_action(navigation, "Quit", self._quit)
        add_action(gameplay, "Claim draw", self.claim_draw)
        add_action(gameplay, "Resign", self.resign_game)
        add_action(gameplay, "Export", self.export_game)
        add_action(gameplay, "Notation", self.export_notation)

        body = ttk.Frame(self)
        body.grid(row=1, column=0, sticky="nsew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, minsize=280)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        self.top_player = PlayerView(left, -1)
        self.top_player.grid(row=0, column=0, sticky="ew")
        ttk.Label(left, textvariable=self.turn, font=("TkDefaultFont", 12)).grid(
            row=1, column=0, sticky="w"
        )
        try:
            config = load_preferences()
        except PreferencesError:
            config = dict(DEFAULTS)
        self._preferred_board_size = config["board_size"]
        self.board_area = ttk.Frame(left)
        self.board_area.grid(row=2, column=0, sticky="nsew")
        self.board_view = BoardView(
            self.board_area,
            self.session.board_projection(),
            on_square_clicked=self.on_square_clicked,
            square_size=self._preferred_board_size,
            show_coordinates=config["show_coordinates"],
        )
        self.board_view.pack(expand=True)
        # Fit to the board's allocated space, rather than its requested Canvas pixels.
        self.board_area.bind("<Configure>", self._resize_board)
        self.bottom_player = PlayerView(left, 1)
        self.bottom_player.grid(row=3, column=0, sticky="ew")

        right = ttk.Frame(body, padding=(12, 0, 0, 0))
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=3)
        right.rowconfigure(3, weight=2)
        ttk.Label(right, text="Quests", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        quest_panel = ttk.Frame(right)
        quest_panel.grid(row=1, column=0, sticky="nsew")
        quest_panel.columnconfigure(0, weight=1)
        quest_panel.rowconfigure(0, weight=1)
        self.quest_viewport = tk.Canvas(
            quest_panel, width=240, height=100, highlightthickness=0, borderwidth=0
        )
        self.quest_viewport.grid(row=0, column=0, sticky="nsew")
        quest_scroll = ttk.Scrollbar(
            quest_panel, orient="vertical", command=self.quest_viewport.yview
        )
        quest_scroll.grid(row=0, column=1, sticky="ns")
        self.quest_viewport.configure(yscrollcommand=quest_scroll.set, takefocus=1)
        quest_content = ttk.Frame(self.quest_viewport)
        self._quest_window = self.quest_viewport.create_window(
            (0, 0), window=quest_content, anchor="nw"
        )
        self.quest_list = QuestList(quest_content)
        self.quest_list.pack(fill="both", expand=True)
        quest_content.bind(
            "<Configure>",
            lambda _event: self.quest_viewport.configure(
                scrollregion=self.quest_viewport.bbox("all")
            ),
        )
        self.quest_viewport.bind(
            "<Configure>",
            lambda event: self.quest_viewport.itemconfigure(self._quest_window, width=event.width),
        )
        self.quest_viewport.bind(
            "<Prior>", lambda _event: self.quest_viewport.yview_scroll(-1, "pages")
        )
        self.quest_viewport.bind(
            "<Next>", lambda _event: self.quest_viewport.yview_scroll(1, "pages")
        )
        self.quest_viewport.bind(
            "<Up>", lambda _event: self.quest_viewport.yview_scroll(-1, "units")
        )
        self.quest_viewport.bind(
            "<Down>", lambda _event: self.quest_viewport.yview_scroll(1, "units")
        )
        self.quest_viewport.bind(
            "<Button-4>", lambda _event: self.quest_viewport.yview_scroll(-3, "units")
        )
        self.quest_viewport.bind(
            "<Button-5>", lambda _event: self.quest_viewport.yview_scroll(3, "units")
        )
        self.quest_viewport.bind("<MouseWheel>", self._scroll_quests)

        ttk.Label(right, text="Moves", font=("TkDefaultFont", 12, "bold")).grid(
            row=2, column=0, sticky="w", pady=(6, 0)
        )
        history_panel = ttk.Frame(right)
        history_panel.grid(row=3, column=0, sticky="nsew")
        history_panel.columnconfigure(0, weight=1)
        history_panel.rowconfigure(0, weight=1)
        self.history = tk.Listbox(history_panel, height=4, width=24)
        self.history.grid(row=0, column=0, sticky="nsew")
        history_scroll = ttk.Scrollbar(history_panel, orient="vertical", command=self.history.yview)
        history_scroll.grid(row=0, column=1, sticky="ns")
        self.history.configure(yscrollcommand=history_scroll.set)
        # A long save path must not expand the minimum window beyond its viewport.
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", width=1).grid(
            row=2, column=0, sticky="ew", pady=(6, 0)
        )

    def _resize_board(self, event: tk.Event) -> None:
        self._fit_board(event.width, event.height)

    def _fit_board(self, width: int | None = None, height: int | None = None) -> None:
        # Padding belongs to the host, not the board. Preserve square pixels
        # and use the same size for Canvas hit-testing and drawing.
        width = self.board_area.winfo_width() if width is None else width
        height = self.board_area.winfo_height() if height is None else height
        self.board_view.fit_to(max(1, width), max(1, height - 8), self._preferred_board_size)

    def _scroll_quests(self, event: tk.Event) -> None:
        if event.delta:
            direction = -1 if event.delta > 0 else 1
            self.quest_viewport.yview_scroll(direction * max(1, abs(event.delta) // 120), "units")

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
        self._fit_board()
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
        self._preferred_board_size = values["board_size"]
        self.board_view.show_coordinates = values["show_coordinates"]
        self._fit_board()
        self.board_view.refresh()

    def open_game(self) -> None:
        source = filedialog.askopenfilename(parent=self, filetypes=[("Saved games", "*.json")])
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

    def resign_game(self) -> None:
        """End the active player's game using the authoritative result rules."""
        state = self.session.snapshot()
        if state["outcome"] is not None:
            return
        side = state["active_side"]
        who = "White" if side == 1 else "Black"
        if not messagebox.askyesno("Resign", f"{who}: resign this game?", parent=self):
            return
        actor = state["participants"][str(side)]
        try:
            self.session.submit(actor, state["revision"], {"type": "resign"})
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Resign", str(error), parent=self)
            return
        self.window_controller.game_controller.reset_selection()
        self.refresh()

    def claim_draw(self) -> None:
        """Try only named game-owned claim conditions; do not grant local draws."""
        state = self.session.snapshot()
        if state["outcome"] is not None:
            return
        named = [
            rule["id"]
            for rule in state["config"]["rules"]
            if rule["hook"] == "outcome"
            and ("claim" in rule["id"] or "threefold" in rule["id"] or "fifty" in rule["id"])
        ]
        if not named:
            messagebox.showinfo(
                "Claim draw", "No draw claims are defined for this game.", parent=self
            )
            return
        options = "\\n".join(f"{i + 1}. {name}" for i, name in enumerate(named))
        selected = simpledialog.askinteger(
            "Claim draw",
            "Select a configured draw claim:\\n" + options,
            parent=self,
            minvalue=1,
            maxvalue=len(named),
        )
        if selected is None:
            return
        actor = state["participants"][str(state["active_side"])]
        try:
            self.session.submit(
                actor,
                state["revision"],
                {
                    "type": "claim_draw",
                    "claim": named[selected - 1],
                    "intended_move": None,
                },
            )
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Claim draw", str(error), parent=self)
            return
        self.window_controller.game_controller.reset_selection()
        self.refresh()

    def export_notation(self) -> None:
        supported = self.session.snapshot()["config"]["exports"]
        if len(supported) != 1 or supported[0] not in ("pgn", "pdn"):
            messagebox.showerror(
                "Notation", "This game has no supported notation export.", parent=self
            )
            return
        extension = "." + supported[0]
        destination = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=extension,
            filetypes=[("Game notation", "*" + extension)],
        )
        if not destination:
            return
        try:
            save_notation(self.session, destination)
        except (OSError, NotationError, ValueError) as error:
            messagebox.showerror("Notation", str(error), parent=self)
            return
        self.status.set(f"Exported notation to {destination}")

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
