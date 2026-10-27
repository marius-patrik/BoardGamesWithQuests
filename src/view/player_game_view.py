"""Tkinter gameplay sourced exclusively from detached JSON session snapshots."""

from __future__ import annotations

import json
from model.game.persistence import SessionFileError, load_session, save_session
from model.game.notation import NotationError, save_notation
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

from controller.window_controller import WindowController, display_game_name
from model.game.preferences import DEFAULTS, PreferencesError, load_preferences
from view.game_view import BoardView
from view.player_view import PlayerView
from view.quest_view import QuestList

REFRESH_INTERVAL_MS = 500

OUTCOME_CAUSES = {
    "resignation": "resignation",
    "resignation-draw": "resignation with insufficient winning material",
    "checkmate": "checkmate",
    "stalemate": "stalemate",
    "no_legal_moves": "no legal moves",
    "timeout": "time expired",
    "agreement": "mutual agreement",
    "threefold": "threefold repetition",
    "fivefold": "fivefold repetition",
    "fifty-move": "fifty-move rule",
    "forty-move": "40-move rule",
    "seventy-five-move": "seventy-five-move rule",
    "dead-material": "insufficient mating material",
    "same-color-bishops": "insufficient mating material",
}


def outcome_description(state: dict[str, Any]) -> str:
    """Render the committed result, without inferring terminal rules in the UI."""
    outcome = state["outcome"]
    if outcome is None:
        return ""
    cause = outcome["cause"]
    if cause.startswith("timeout-draw-"):
        reason = "time expired with insufficient winning material"
    elif cause.startswith("timeout-win-"):
        reason = "time expired"
    else:
        reason = OUTCOME_CAUSES.get(cause, cause.replace("_", " ").replace("-", " "))
    if outcome["kind"] == "draw":
        return f"Draw — {reason}."
    winner = outcome.get("winner")
    if winner is None:
        return f"Game finished — {reason}."
    participants = state["participants"]
    if winner in (1, "1", participants["1"]):
        side = "White"
    elif winner in (-1, "-1", participants["-1"]):
        side = "Black"
    else:
        side = str(winner)
    return f"{side} wins — {reason}."


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
        self._presented_terminal_key: tuple[str, int] | None = None
        # Save-point metadata only: never a duplicate authoritative game snapshot.
        self._saved_state_key = self._state_key(self.session.snapshot())
        self._build_layout(square_size)
        self.refresh()

    @staticmethod
    def _state_key(state: dict[str, Any]) -> tuple[str, int]:
        return state["game_id"], state["revision"]

    def _mark_clean(self) -> None:
        self._saved_state_key = self._state_key(self.session.snapshot())

    def _has_unsaved_progress(self) -> bool:
        state = self.session.snapshot()
        return state["revision"] > 0 and self._state_key(state) != self._saved_state_key

    def _confirm_replace(self) -> bool:
        """Protect an in-progress game before another session can replace it."""
        if not self._has_unsaved_progress():
            return True
        answer = messagebox.askyesnocancel(
            "Unsaved game",
            "Save the current game before replacing it?\n\n"
            "Yes: Save a game file\nNo: Discard progress\nCancel: Keep playing",
            parent=self,
            default=messagebox.CANCEL,
        )
        if answer is None:
            return False
        if answer is False:
            return True
        return self.export_game()

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
        add_action(gameplay, "Offer draw", self.offer_draw)
        add_action(gameplay, "Respond draw", self.respond_draw)
        add_action(gameplay, "Resign", self.resign_game)
        add_action(gameplay, "Export", self.export_game)
        add_action(gameplay, "Notation", self.export_notation)

        # The reference GUI places both participants BESIDE the board. The
        # center column owns all remaining width; quests scroll separately.
        body = ttk.Frame(self)
        body.grid(row=1, column=0, sticky="nsew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, minsize=170)
        body.columnconfigure(2, minsize=448)
        body.columnconfigure(3, minsize=170)
        body.columnconfigure(4, weight=1)
        self._body = body

        self.player_views: dict[int, PlayerView] = {}
        self.quest_lists: dict[int, QuestList] = {}
        self.quest_viewports: dict[int, tk.Canvas] = {}

        for side, column in ((1, 1), (-1, 3)):
            pane = ttk.Frame(body, padding=(3, 0))
            pane.grid(row=0, column=column, sticky="nsew")
            pane.columnconfigure(0, weight=1)
            pane.rowconfigure(2, weight=1)
            player = PlayerView(pane, side)
            player.grid(row=0, column=0, sticky="ew")
            self.player_views[side] = player
            ttk.Separator(pane).grid(row=1, column=0, sticky="ew", pady=4)

            quests_host = ttk.LabelFrame(pane, text="Your quests", padding=(2, 2))
            quests_host.grid(row=2, column=0, sticky="nsew")
            quests_host.columnconfigure(0, weight=1)
            quests_host.rowconfigure(0, weight=1)
            viewport = tk.Canvas(
                quests_host, width=142, height=60, highlightthickness=0, borderwidth=0
            )
            viewport.grid(row=0, column=0, sticky="nsew")
            scroll = ttk.Scrollbar(quests_host, orient="vertical", command=viewport.yview)
            scroll.grid(row=0, column=1, sticky="ns")
            viewport.configure(yscrollcommand=scroll.set, takefocus=1)
            content = ttk.Frame(viewport)
            window_id = viewport.create_window((0, 0), window=content, anchor="nw")
            listing = QuestList(content, side)
            listing.pack(fill="both", expand=True)
            content.bind(
                "<Configure>",
                lambda _event, target=viewport: target.configure(scrollregion=target.bbox("all")),
            )
            viewport.bind(
                "<Configure>",
                lambda event, target=viewport, identifier=window_id: target.itemconfigure(
                    identifier, width=event.width
                ),
            )
            viewport.bind(
                "<Prior>",
                lambda _event, target=viewport: target.yview_scroll(-1, "pages"),
            )
            viewport.bind(
                "<Next>",
                lambda _event, target=viewport: target.yview_scroll(1, "pages"),
            )
            viewport.bind(
                "<Up>",
                lambda _event, target=viewport: target.yview_scroll(-1, "units"),
            )
            viewport.bind(
                "<Down>",
                lambda _event, target=viewport: target.yview_scroll(1, "units"),
            )
            viewport.bind(
                "<Button-4>",
                lambda _event, target=viewport: target.yview_scroll(-3, "units"),
            )
            viewport.bind(
                "<Button-5>",
                lambda _event, target=viewport: target.yview_scroll(3, "units"),
            )
            viewport.bind(
                "<MouseWheel>",
                lambda event, target=viewport: self._scroll_quests(event, target),
            )
            self.quest_lists[side] = listing
            self.quest_viewports[side] = viewport

        # Retain existing consumer attributes while the source-tree rename
        # remains the separate #462 task.
        self.top_player = self.player_views[-1]
        self.bottom_player = self.player_views[1]
        self.quest_viewport = self.quest_viewports[1]
        self.quest_list = self.quest_lists[1]

        center = ttk.Frame(body, padding=(4, 0))
        center.grid(row=0, column=2, sticky="nsew")
        center.rowconfigure(1, weight=1)
        center.columnconfigure(0, weight=1)
        ttk.Label(
            center,
            textvariable=self.turn,
            font=("TkDefaultFont", 11),
            anchor="center",
            wraplength=330,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 3))
        try:
            config = load_preferences()
        except PreferencesError:
            config = dict(DEFAULTS)
        self._preferred_board_size = config["board_size"]
        self.board_area = ttk.Frame(center)
        self.board_area.grid(row=1, column=0, sticky="nsew")
        self.board_view = BoardView(
            self.board_area,
            self.session.board_projection(),
            on_square_clicked=self.on_square_clicked,
            square_size=self._preferred_board_size,
            show_coordinates=config["show_coordinates"],
        )
        self.board_view.pack(expand=True)
        self.board_area.bind("<Configure>", self._resize_board)

        # History remains the existing simple, scrollable list. Its deeper
        # redesign is reserved for #453.
        history_panel = ttk.LabelFrame(self, text="Moves")
        history_panel.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        history_panel.columnconfigure(0, weight=1)
        self.history = tk.Listbox(history_panel, height=3)
        self.history.grid(row=0, column=0, sticky="ew")
        history_scroll = ttk.Scrollbar(history_panel, orient="vertical", command=self.history.yview)
        history_scroll.grid(row=0, column=1, sticky="ns")
        self.history.configure(yscrollcommand=history_scroll.set)
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", width=1).grid(
            row=3, column=0, sticky="ew", pady=(4, 0)
        )

    def _resize_board(self, event: tk.Event) -> None:
        self._fit_board(event.width, event.height)

    def _fit_board(self, width: int | None = None, height: int | None = None) -> None:
        # Keep the whole player/board/player cluster centered in spacious
        # windows, and shrink only the middle column at compact widths.
        available = max(
            self.board_view.board.cols * 32,
            self._body.winfo_width() - 2 * 170 - 20,
        )
        desired = min(self.board_view.board.cols * self._preferred_board_size, available)
        self._body.columnconfigure(2, minsize=desired)
        width = self.board_area.winfo_width() if width is None else width
        height = self.board_area.winfo_height() if height is None else height
        self.board_view.fit_to(max(1, width), max(1, height - 8), self._preferred_board_size)

    def _scroll_quests(self, event: tk.Event, target: tk.Canvas) -> None:
        if event.delta:
            direction = -1 if event.delta > 0 else 1
            target.yview_scroll(direction * max(1, abs(event.delta) // 120), "units")

    def on_square_clicked(self, position: tuple[int, int]) -> None:
        if self.session.snapshot()["outcome"] is not None:
            return
        result = self.window_controller.on_square_clicked(position)
        if result["action"] == "choose":
            options = result["options"]
            choice = self._choose_complete_move(
                options,
                self.session.snapshot(),
                title="Choose your move",
                explanation="Select a complete capture route or promotion:",
                confirm_label="Play selected move",
            )
            if choice is None:
                self.window_controller.set_status(
                    "Move choice canceled. Select a destination or another piece."
                )
            else:
                result = self.window_controller.game_controller.submit_move(choice)
                if result["action"] == "moved":
                    self.window_controller.set_status("Move played.")
        controller = self.window_controller.game_controller
        self.board_view.set_selection(controller.selected_square, controller.highlighted_moves)
        if result["action"] == "invalid":
            self.board_view.show_invalid_square(position)
            self.status.set(result.get("message", "Invalid move."))
        self.refresh()

    def reload(self, *, clean: bool = False) -> None:
        """Redraw after a real game switch or session reset."""
        self.window_controller.game_controller.reset_selection()
        if clean:
            self._mark_clean()
        self._last_history = None
        self.board_view.set_selection(None, [])
        self.winfo_toplevel().title(self.window_controller.game_title())
        self.refresh()

    def on_new_game(self) -> None:
        if not self._confirm_replace():
            return
        if self.on_new_game_request is not None:
            self.on_new_game_request()
            return
        self.window_controller.game_controller.new_game()
        self.reload(clean=True)

    @staticmethod
    def _label(square: list[int], rows: int) -> str:
        return f"{chr(ord('a') + square[1])}{rows - square[0]}"

    def _refresh_actions(self, state: dict[str, Any]) -> None:
        """Controls reflect the committed session, not a parallel UI lifecycle."""
        finished = state["outcome"] is not None
        availability = {
            "Resign": not finished,
            "Claim draw": not finished and bool(self.session.configured_draw_claims()),
            "Offer draw": not finished
            and bool(self.session.draw_action_availability()["offer_actors"]),
            "Respond draw": not finished
            and (self.session.draw_action_availability()["response_actor"] is not None),
            "Notation": state["config"]["exports"] in (["pgn"], ["pdn"]),
        }
        for label, enabled in availability.items():
            self.action_buttons[label].configure(state="normal" if enabled else "disabled")
        # New/Open/Export/Settings/Quit remain available after the result is committed.

    def refresh(self) -> None:
        state = self.session.snapshot()
        finished = state["outcome"] is not None
        if finished:
            self.window_controller.game_controller.reset_selection()
            self.board_view.set_selection(None, [])
        self.board_view.set_appearance(
            state["config"].get("appearance", {}),
            draughts=self.session.game == "checkers",
        )
        accepted_moves = [event["move"] for event in state["events"] if event["move"] is not None]
        if accepted_moves:
            last = accepted_moves[-1]
            self.board_view.set_last_move(tuple(last["start"]), tuple(last["hops"][-1]))
        else:
            self.board_view.set_last_move(None, None)

        # The current session only reports the terminal checkmate verdict,
        # not general attack/check state. Never infer check from piece vectors.
        checked_side = (
            state["active_side"]
            if (state["outcome"] is not None and state["outcome"]["cause"] == "checkmate")
            else None
        )
        checked_king = next(
            (
                tuple(piece["square"])
                for piece in state["board"]
                if piece["kind"] == "king" and piece["side"] == checked_side
            ),
            None,
        )
        self.board_view.set_in_check(checked_king)
        self.board_view.refresh(self.session.board_projection())
        self._fit_board()
        remaining = self.session.clock_remaining()
        for player in self.player_views.values():
            player.refresh(state, remaining)
        game_name = display_game_name(self.session.game)
        if finished:
            terminal_key = self._state_key(state)
            if self._presented_terminal_key != terminal_key:
                self._presented_terminal_key = terminal_key
                self.window_controller.set_status(
                    "Game finished. You can save the result or start another game."
                )
            self.turn.set(f"{game_name} · {outcome_description(state)}")
        else:
            self._presented_terminal_key = None
            active = "White" if state["active_side"] == 1 else "Black"
            played = sum(event["move"] is not None for event in state["events"])
            self.turn.set(f"{game_name} · {active} to move · move {played + 1}")
        self.status.set(self.window_controller.status_message or "Ready")
        self._refresh_actions(state)
        for quests in self.quest_lists.values():
            quests.refresh(state)

        events = tuple(json.dumps(entry, sort_keys=True) for entry in state["events"])
        if events != self._last_history:
            self._last_history = events
            self.history.delete(0, tk.END)
            for event in state["events"]:
                move = event.get("move")
                if move is None:
                    kind = event.get("action", {}).get("type", "result")
                    description = {
                        "offer_draw": "Draw offered",
                        "accept_draw": "Draw accepted",
                        "reject_draw": "Draw declined",
                        "claim_draw": "Draw claimed",
                        "resign": "Resignation",
                        "timeout": "Time expired",
                    }.get(kind, kind.replace("_", " ").capitalize())
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
        if not self._confirm_replace():
            return
        source = filedialog.askopenfilename(parent=self, filetypes=[("Saved games", "*.json")])
        if not source:
            return
        try:
            restored = load_session(source)
        except (OSError, SessionFileError, ValueError, TypeError) as error:
            messagebox.showerror(
                "Open game", f"Unable to open the saved game:\n{error}", parent=self
            )
            return
        # Replay verification has completed before the live session is replaced.
        self.window_controller.game_controller.session = restored
        self.window_controller.set_status(f"Opened {display_game_name(restored.game)}.")
        self.reload(clean=True)

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

    def offer_draw(self) -> None:
        """Request a non-withdrawable authoritative offer as an actual participant."""
        state = self.session.snapshot()
        actors = self.session.draw_action_availability()["offer_actors"]
        if not actors:
            return
        if len(actors) == 1:
            actor = actors[0]
        else:
            labels = [
                "White" if actor == state["participants"]["1"] else "Black" for actor in actors
            ]
            choice = simpledialog.askinteger(
                "Offer draw",
                "Choose which participant offers the draw:\n"
                + "\n".join(f"{i + 1}. {name}" for i, name in enumerate(labels)),
                parent=self,
                minvalue=1,
                maxvalue=len(actors),
            )
            if choice is None:
                return
            actor = actors[choice - 1]
        if not messagebox.askyesno(
            "Offer draw",
            "Offer your opponent a draw? The offer cannot be withdrawn.",
            parent=self,
        ):
            return
        try:
            self.session.submit(actor, state["revision"], {"type": "offer_draw"})
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Offer draw", str(error), parent=self)
            return
        self.window_controller.set_status("Draw offered. Waiting for the other player.")
        self.refresh()

    def respond_draw(self) -> None:
        """Let only the other participant accept or decline a persisted offer."""
        state = self.session.snapshot()
        available = self.session.draw_action_availability()
        actor = available["response_actor"]
        if actor is None:
            return
        reply = messagebox.askyesnocancel(
            "Respond to draw",
            "Accept the draw offer?\nYes: accept. No: decline. Cancel: decide later.",
            parent=self,
        )
        if reply is None:
            return
        try:
            self.session.submit(
                actor,
                state["revision"],
                {"type": "accept_draw" if reply else "reject_draw"},
            )
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Respond to draw", str(error), parent=self)
            return
        self.window_controller.set_status("Draw accepted." if reply else "Draw offer declined.")
        self.refresh()

    def _format_complete_move(
        self, move: dict[str, Any], state: dict[str, Any], *, capture_notation: bool = True
    ) -> str:
        """Describe an engine-supplied full action; never reconstruct its route."""
        rows = state["config"]["board"]["rows"]
        points = [move["start"], *move["hops"]]
        occupied = any(
            piece["square"] == move["hops"][-1] and piece["side"] != state["active_side"]
            for piece in state["board"]
        )
        separator = " × " if capture_notation and (len(move["hops"]) > 1 or occupied) else " → "
        route = separator.join(self._label(point, rows) for point in points)
        promotion = move.get("promotion")
        if promotion is not None:
            kind = str(promotion)
            route += f"  —  Promote to {kind.replace('_', ' ').title()}"
        return route

    def _choose_complete_move(
        self,
        moves: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        title: str,
        explanation: str,
        confirm_label: str,
        capture_notation: bool = True,
    ) -> dict[str, Any] | None:
        """Choose exactly one authoritative complete DTO with a real Tk listbox."""
        if not moves:
            return None
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self.winfo_toplevel())
        dialog.resizable(True, True)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=explanation, wraplength=420).pack(anchor="w", pady=(0, 8))
        holder = ttk.Frame(frame)
        holder.pack(fill="both", expand=True)
        listbox = tk.Listbox(
            holder,
            exportselection=False,
            width=54,
            height=min(12, max(4, len(moves))),
            activestyle="dotbox",
        )
        scroll = ttk.Scrollbar(holder, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scroll.set)
        listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for index, move in enumerate(moves, start=1):
            description = self._format_complete_move(move, state, capture_notation=capture_notation)
            listbox.insert(tk.END, f"{index}. {description}")

        selected: list[dict[str, Any] | None] = [None]

        def finish(accept: bool) -> None:
            if accept and listbox.curselection():
                selected[0] = moves[listbox.curselection()[0]]
            dialog.destroy()

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(8, 0))
        ttk.Button(controls, text="Cancel", command=lambda: finish(False)).pack(
            side="right", padx=(8, 0)
        )
        ttk.Button(controls, text=confirm_label, command=lambda: finish(True)).pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", lambda: finish(False))
        dialog.bind("<Escape>", lambda _event: finish(False))
        dialog.bind("<Return>", lambda _event: finish(True))
        listbox.bind("<Double-Button-1>", lambda _event: finish(True))
        dialog.update_idletasks()
        dialog.grab_set()
        listbox.selection_set(0)
        listbox.activate(0)
        listbox.focus_set()
        self.wait_window(dialog)
        return selected[0]

    def _choose_intended_move(
        self, moves: list[dict[str, Any]], rows: int
    ) -> dict[str, Any] | None:
        """Keep #438's claim chooser semantics: choose an intent, never play it."""
        state = self.session.snapshot()
        return self._choose_complete_move(
            moves,
            state,
            title="Intended move for draw claim",
            explanation="Choose the full legal route to claim without playing that move:",
            confirm_label="Use intended move",
            capture_notation=False,
        )

    def claim_draw(self) -> None:
        """Try only named game-owned claim conditions; do not grant local draws."""
        state = self.session.snapshot()
        if state["outcome"] is not None:
            return
        named = self.session.configured_draw_claims()
        if not named:
            messagebox.showinfo(
                "Claim draw", "No draw claims are defined for this game.", parent=self
            )
            return
        options = "\n".join(
            f"{i + 1}. {OUTCOME_CAUSES.get(name, name.replace('-', ' ').title())}"
            for i, name in enumerate(named)
        )
        selected = simpledialog.askinteger(
            "Claim draw",
            "Choose a draw claim (the game verifies eligibility):\n" + options,
            parent=self,
            minvalue=1,
            maxvalue=len(named),
        )
        if selected is None:
            return
        claim = named[selected - 1]
        try:
            eligibility = self.session.draw_claim_candidates(claim)
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Claim draw", str(error), parent=self)
            return
        intended_move = None
        prospective = eligibility["intended_moves"]
        if eligibility["current"] and prospective:
            choice = messagebox.askyesnocancel(
                "Claim draw",
                "Claim the current position? Yes: claim now. No: choose an intended move.",
                parent=self,
            )
            if choice is None:
                return
            if not choice:
                intended_move = self._choose_intended_move(
                    prospective, state["config"]["board"]["rows"]
                )
                if intended_move is None:
                    return
        elif not eligibility["current"] and prospective:
            intended_move = self._choose_intended_move(
                prospective, state["config"]["board"]["rows"]
            )
            if intended_move is None:
                return
        actor = state["participants"][str(state["active_side"])]
        try:
            self.session.submit(
                actor,
                state["revision"],
                {
                    "type": "claim_draw",
                    "claim": claim,
                    "intended_move": intended_move,
                },
            )
        except (ValueError, RuntimeError) as error:
            messagebox.showerror(
                "Claim draw", f"That draw claim is not available:\n{error}", parent=self
            )
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
        self.window_controller.set_status(f"Exported notation to {destination}")
        self.status.set(self.window_controller.status_message)

    def export_game(self) -> bool:
        """Use the existing validated atomic session exporter as the Save action."""
        destination = filedialog.asksaveasfilename(
            parent=self, defaultextension=".json", filetypes=[("Saved games", "*.json")]
        )
        if not destination:
            return False
        try:
            save_session(self.session, destination)
        except (OSError, SessionFileError, ValueError) as error:
            messagebox.showerror("Save game", f"Unable to save the game:\n{error}", parent=self)
            return False
        self._mark_clean()
        self.window_controller.set_status(f"Saved game to {destination}")
        self.status.set(self.window_controller.status_message)
        return True

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
