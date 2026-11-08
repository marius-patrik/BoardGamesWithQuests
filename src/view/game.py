"""Accessible 8×8 Tkinter Button board; never modifies game state directly."""

from __future__ import annotations
import sys
import tkinter as tk
from model.board import Square
from model.manager import GameManager
from model.piece import SYMBOLS

LIGHT = "#ede8dc"
DARK = "#9d9280"
SELECTED = "#e3bb4b"
DESTINATION = "#abcab0"


class GameView(tk.Frame):
    def __init__(self, parent, on_square):
        super().__init__(parent, bg="#fafaf8")
        self.on_square = on_square
        self.buttons: dict[Square, tk.Button] = {}
        font_family = "Segoe UI Symbol" if sys.platform == "win32" else "DejaVu Sans"
        self.font_family = font_family
        tk.Label(self, text="", bg="#fafaf8", width=2).grid(row=0, column=0)
        for c in range(8):
            tk.Label(self, text=chr(97 + c), fg="#51565b", bg="#fafaf8", font=("Arial", 10)).grid(
                row=9, column=c + 1, sticky="nsew"
            )
        for r in range(8):
            tk.Label(self, text=str(8 - r), fg="#51565b", bg="#fafaf8", font=("Arial", 10)).grid(
                row=r + 1, column=0, sticky="nsew"
            )
            for c in range(8):
                square = (r, c)
                button = tk.Button(
                    self,
                    text="",
                    width=2,
                    height=1,
                    font=(font_family, 24),
                    takefocus=True,
                    relief="flat",
                    bd=0,
                    highlightthickness=2,
                    highlightbackground="#fafaf8",
                    highlightcolor="#24618d",
                    command=lambda s=square: self.on_square(s),
                )
                button.grid(row=r + 1, column=c + 1, sticky="nsew", padx=1, pady=1)
                button.bind("<Up>", lambda e, s=square: self._focus((max(0, s[0] - 1), s[1])))
                button.bind("<Down>", lambda e, s=square: self._focus((min(7, s[0] + 1), s[1])))
                button.bind("<Left>", lambda e, s=square: self._focus((s[0], max(0, s[1] - 1))))
                button.bind("<Right>", lambda e, s=square: self._focus((s[0], min(7, s[1] + 1))))
                button.bind("<Return>", lambda e, b=button: b.invoke())
                button.bind("<space>", lambda e, b=button: b.invoke())
                self.buttons[square] = button
            self.grid_rowconfigure(r + 1, weight=1)
        for c in range(1, 9):
            self.grid_columnconfigure(c, weight=1)

    def _focus(self, s: Square) -> str:
        self.buttons[s].focus_set()
        return "break"

    def vykresli_desku(
        self,
        manager: GameManager,
        selected: Square | None = None,
        destinations: tuple[Square, ...] = (),
    ) -> None:
        for s, button in self.buttons.items():
            piece = manager.plocha.vrat_obsah(s)
            light = (s[0] + s[1]) % 2 == 0
            bg = (
                SELECTED
                if selected == s
                else DESTINATION if s in destinations else LIGHT if light else DARK
            )
            fg = (
                ("#fafafa" if not light else "#37414a")
                if piece and piece.barva == "white"
                else "#1d2831"
            )
            button.config(
                text=SYMBOLS[piece.barva][piece.kod] if piece else " ",
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                disabledforeground=fg,
            )
            # Preserve focusability even in a finished match for examination.

    def zvyrazni_tahy(
        self,
        manager: GameManager,
        selected: Square | None,
        destinations: tuple[Square, ...],
    ):
        self.vykresli_desku(manager, selected, destinations)
