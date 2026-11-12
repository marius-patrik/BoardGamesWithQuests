"""Single-window Chess application: setup, gameplay, dialogs and persistence feedback."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from model.board import Square, algebraicky
from model.manager import GameManager
from model.user import UserManager
from controller.controller import GameManagerController
from view.game import GameView
from view.panel import HracGameView

BACKGROUND = "#e9ebed"
PAPER = "#fafaf8"
INK = "#242a31"


class BoardGamesApplication(tk.Tk):
    """One Tk root: setup, live match, focused promotion and save feedback.

    The controller owns ephemeral selection; GameManager owns committed Chess
    state; display refreshes never directly apply rules or award experience.
    """

    def __init__(self, data_root: Path | None = None):
        super().__init__()
        self.title("BoardGamesWithQuests · Chess")
        self.geometry("1110x820")
        self.minsize(850, 660)
        self.configure(bg=BACKGROUND)
        self.users = UserManager(data_root)
        self.manager: GameManager | None = None
        self.controller: GameManagerController | None = None
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        self.style.configure("TButton", padding=(12, 7))
        self.style.configure("TCombobox", padding=(5, 6))
        self.main = tk.Frame(self, bg=BACKGROUND)
        self.main.pack(fill="both", expand=True)
        self.bind("<Control-Return>", self._start_match_shortcut)
        self.bind("<Control-r>", self._resign_shortcut)
        self.show_setup()

    def _clear(self) -> None:
        for child in self.main.winfo_children():
            child.destroy()

    def show_setup(self) -> None:
        self._clear()
        container = tk.Frame(
            self.main,
            bg=PAPER,
            padx=28,
            pady=22,
            highlightbackground="#d9dbdf",
            highlightthickness=1,
        )
        container.pack(expand=True, fill="none", padx=16, pady=16)
        tk.Label(
            container,
            text="BOARDGAMES WITH QUESTS",
            font=("Arial", 11, "bold"),
            bg=PAPER,
            fg="#4c6d81",
        ).pack(anchor="w")
        tk.Label(
            container,
            text="Chess · Local match",
            font=("Arial", 23, "bold"),
            bg=PAPER,
            fg=INK,
        ).pack(anchor="w", pady=(8, 3))
        tk.Label(
            container,
            text="Choose two different local profiles, or create one below.",
            font=("Arial", 10),
            bg=PAPER,
            fg="#626a74",
        ).pack(anchor="w", pady=(0, 19))
        names = sorted(self.users.uzivatele)
        self.seat_choices = {}
        for color in ("white", "black"):
            tk.Label(
                container,
                text=color.title() + " player",
                bg=PAPER,
                fg=INK,
                font=("Arial", 11, "bold"),
            ).pack(anchor="w", pady=(8, 3))
            box = ttk.Combobox(container, values=names, state="readonly", width=38)
            box.pack(fill="x", ipady=2)
            if len(names) > (0 if color == "white" else 1):
                box.set(names[0 if color == "white" else 1])
            self.seat_choices[color] = box
        ttk.Separator(container).pack(fill="x", pady=17)
        tk.Label(
            container,
            text="Create local profile",
            bg=PAPER,
            fg=INK,
            font=("Arial", 12, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        self.username = ttk.Entry(container, width=38)
        self.username.pack(fill="x", pady=3)
        self.username.insert(0, "")
        self.display_name = ttk.Entry(container, width=38)
        self.display_name.pack(fill="x", pady=3)
        self.profile_hint = tk.Label(
            container,
            text="Username (first field) · Display name (second field)",
            font=("Arial", 9),
            bg=PAPER,
            fg="#626a74",
        )
        self.profile_hint.pack(anchor="w")
        ttk.Button(container, text="Create profile", command=self.create_profile).pack(
            fill="x", pady=(8, 13)
        )
        ttk.Button(container, text="Start new game →  (Ctrl+Enter)", command=self.start_match).pack(
            fill="x", pady=(6, 4)
        )
        self.setup_status = tk.Label(
            container,
            text=self.users.save_error or "Offline · Local data only",
            bg=PAPER,
            fg="#a53e35" if self.users.save_error else "#60706a",
            wraplength=380,
            justify="left",
        )
        self.setup_status.pack(anchor="w", pady=(9, 0))
        self.after_idle(lambda: self.username.focus_set() if self.username.winfo_exists() else None)

    def create_profile(self) -> None:
        previous_seats = {color: box.get() for color, box in self.seat_choices.items()}
        try:
            user = self.users.vytvor_uzivatele(self.username.get(), self.display_name.get())
        except ValueError as exc:
            messagebox.showerror("Invalid profile", str(exc), parent=self)
            return
        self.show_setup()
        for color, username in previous_seats.items():
            if username in self.users.uzivatele:
                self.seat_choices[color].set(username)
        for color, box in self.seat_choices.items():
            if not box.get():
                box.set(user.uzivatelske_jmeno)
                break
        if self.users.save_error:
            self.setup_status.config(text=self.users.save_error, fg="#a53e35")

    def _start_match_shortcut(self, _event: tk.Event | None = None) -> str:
        """Let the user start a prepared match without finding the mouse button."""
        if self.manager is None:
            self.start_match()
        return "break"

    def start_match(self) -> None:
        white, black = (self.seat_choices[color].get() for color in ("white", "black"))
        try:
            self.manager = GameManager(self.users, white, black)
        except ValueError as exc:
            messagebox.showerror("Cannot start match", str(exc), parent=self)
            return
        self.controller = GameManagerController(self.manager, self.refresh)
        self.show_game()

    def show_game(self) -> None:
        """Compose the match screen; all widgets read one committed manager."""
        self._clear()
        assert self.manager is not None and self.controller is not None
        self._build_game_header()
        self._build_game_toolbar()
        self._build_game_content()
        self._build_game_history()
        self._build_game_persistence()
        self.refresh()

    def _build_game_header(self) -> None:
        header = tk.Frame(self.main, bg=INK, padx=18, pady=10)
        header.pack(fill="x")
        tk.Label(
            header,
            text="BOARDGAMES WITH QUESTS",
            font=("Arial", 11, "bold"),
            fg="#e7ebf0",
            bg=INK,
        ).pack(side="left")
        self.turn = tk.Label(header, text="", font=("Arial", 11, "bold"), fg="#f2cc77", bg=INK)
        self.turn.pack(side="right")

    def _build_game_toolbar(self) -> None:
        toolbar = tk.Frame(self.main, bg=BACKGROUND, padx=12, pady=8)
        toolbar.pack(fill="x")
        for text, command in (
            ("New Game", self.new_game),
            ("Players", self.players_setup),
            ("Clear selection", self.controller.zrus_vyber),
            ("Resign", self.resign),
        ):
            b = ttk.Button(toolbar, text=text, command=command)
            b.pack(side="left", padx=3)
            if text == "Resign":
                self.resign_button = b

    def _build_game_content(self) -> None:
        central = tk.Frame(self.main, bg=BACKGROUND)
        central.pack(fill="both", expand=True, padx=12, pady=(3, 5))
        central.grid_columnconfigure(0, weight=1, uniform="sides")
        central.grid_columnconfigure(1, weight=3)
        central.grid_columnconfigure(2, weight=1, uniform="sides")
        central.grid_rowconfigure(0, weight=1)
        self.white_panel = HracGameView(central, "white")
        self.white_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        board_frame = tk.Frame(
            central,
            bg=PAPER,
            padx=8,
            pady=8,
            highlightbackground="#d6d6d1",
            highlightthickness=1,
        )
        board_frame.grid(row=0, column=1, sticky="nsew")
        self.board = GameView(board_frame, self.on_square)
        self.board.pack(expand=True)
        self.black_panel = HracGameView(central, "black")
        self.black_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

    def _build_game_history(self) -> None:
        bottom = tk.Frame(self.main, bg=PAPER, padx=12, pady=7)
        bottom.pack(fill="x", padx=12, pady=(3, 8))
        tk.Label(
            bottom,
            text="MOVE HISTORY",
            font=("Arial", 9, "bold"),
            bg=PAPER,
            fg="#69717b",
        ).pack(anchor="w")
        self.history = tk.Text(
            bottom,
            height=3,
            wrap="word",
            font=("Arial", 10),
            state="disabled",
            bg=PAPER,
            fg=INK,
            bd=0,
        )
        self.history.pack(fill="x")
        self.status = tk.Label(
            bottom,
            text="",
            font=("Arial", 10),
            bg=PAPER,
            fg="#314e5b",
            anchor="w",
            wraplength=1050,
            justify="left",
        )
        self.status.pack(fill="x", pady=(6, 1))

    def _build_game_persistence(self) -> None:
        warning = tk.Frame(self.main, bg=BACKGROUND, padx=12, pady=5)
        warning.pack(fill="x")
        self.persist_warning = tk.Label(
            warning,
            text="",
            bg=BACKGROUND,
            fg="#ad4037",
            font=("Arial", 9),
            anchor="w",
            justify="left",
        )
        self.persist_warning.pack(side="left", fill="x", expand=True)
        ttk.Button(warning, text="Retry profiles", command=self.retry_profiles).pack(
            side="right", padx=3
        )
        ttk.Button(warning, text="Retry history", command=self.retry_history).pack(
            side="right", padx=3
        )

    def on_square(self, square: Square) -> None:
        assert self.controller is not None
        options = self.controller.vyber_pole(square)
        if options:
            self.ask_promotion()

    def ask_promotion(self) -> None:
        """Commit only the selected promotion; Escape discards pending input."""
        assert self.controller is not None
        dlg = tk.Toplevel(self)
        dlg.title("Pawn promotion")
        dlg.transient(self)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(bg=PAPER)
        tk.Label(
            dlg,
            text="Choose a promotion piece",
            font=("Arial", 12, "bold"),
            bg=PAPER,
            fg=INK,
        ).pack(padx=20, pady=(16, 10))
        controls = tk.Frame(dlg, bg=PAPER)
        controls.pack(padx=15, pady=(0, 13))

        def choose(piece):
            self.controller.potvrd_promenu(piece)
            dlg.destroy()

        for code, caption in (
            ("Q", "Queen"),
            ("R", "Rook"),
            ("B", "Bishop"),
            ("N", "Knight"),
        ):
            ttk.Button(controls, text=caption, command=lambda p=code: choose(p)).pack(
                side="left", padx=3
            )

        def cancel(event=None):
            # Clear the pending promotion as well as the modal, without committing a move.
            self.controller.zrus_vyber()
            dlg.destroy()

        dlg.bind("<Escape>", cancel)
        dlg.protocol("WM_DELETE_WINDOW", cancel)
        dlg.focus_set()

    def _resign_shortcut(self, _event: tk.Event | None = None) -> str:
        """Open the same confirmation as the visible Resign button."""
        if self.manager is not None:
            self.resign()
        return "break"

    def resign(self) -> None:
        assert self.controller is not None and self.manager is not None
        if self.manager.stav == "terminal":
            return
        if messagebox.askyesno(
            "Confirm resignation",
            f"{self.manager.aktivni_hrac.uzivatel.jmeno}, resign this match?",
            parent=self,
        ):
            self.controller.odstup()

    def new_game(self) -> None:
        assert self.controller is not None
        if messagebox.askyesno(
            "New match", "Start a fresh match with the same players?", parent=self
        ):
            self.controller.novou_hru()

    def players_setup(self) -> None:
        if messagebox.askyesno(
            "Change players",
            "Leave this match and return to player selection?",
            parent=self,
        ):
            self.manager = None
            self.controller = None
            self.show_setup()

    def retry_profiles(self) -> None:
        self.users.uloz_uzivatele()
        if self.manager is None:
            # Reload setup choices/status after repairing a profile file on disk.
            self.show_setup()
        else:
            self.refresh()

    def retry_history(self) -> None:
        if self.manager:
            self.manager.logger.uloz_historii()
            self.refresh()

    def refresh(self) -> None:
        """Render the current authoritative match and independent save statuses."""
        if (
            not self.manager
            or not self.controller
            or not hasattr(self, "board")
            or not self.board.winfo_exists()
        ):
            return
        self.manager = self.controller.manager
        manager = self.manager
        self.board.vykresli_desku(manager, self.controller.vybrane, self.controller.destinace)
        self.white_panel.zobraz_hrace(manager)
        self.black_panel.zobraz_hrace(manager)
        self._render_turn(manager)
        self._render_history(manager)
        self._render_persistence_status(manager)

    def _render_turn(self, m: GameManager) -> None:
        if m.stav == "terminal":
            winner = m.hraci[m.winner].uzivatel.jmeno if m.winner else "Neither player"
            self.turn.config(text=f"GAME OVER · {winner} · {m.reason}")
            self.resign_button.state(["disabled"])
        else:
            self.turn.config(
                text=f"{m.aktivni_hrac.uzivatel.jmeno} to move"
                + (" · CHECK" if m.revizor.v_sachu(m.plocha, m.aktivni_barva) else "")
            )
            self.resign_button.state(["!disabled"])

    def _render_history(self, m: GameManager) -> None:
        self.history.config(state="normal")
        self.history.delete("1.0", "end")
        for event in m.logger.events:
            if event["type"] == "move":
                text = f"{event['index']}. {event['actor']}: {algebraicky(tuple(event['from']))} → {algebraicky(tuple(event['to']))}"
                if event["promotion"]:
                    text += "=" + event["promotion"]
                if event["xp_awarded"]:
                    text += f" (+{event['xp_awarded']} XP)"
            else:
                text = f"{event['index']}. {event['actor']} resigned"
            self.history.insert("end", text + "     ")
        self.history.see("end")
        self.history.config(state="disabled")
        self.status.config(text=self.controller.last_message)

    def _render_persistence_status(self, m: GameManager) -> None:
        messages = [e for e in (self.users.save_error, m.logger.save_error) if e]
        self.persist_warning.config(
            text=(" | ".join(messages) if messages else "Local profiles and match history saved"),
            fg="#ad4037" if messages else "#276349",
        )


def run() -> None:
    BoardGamesApplication().mainloop()
