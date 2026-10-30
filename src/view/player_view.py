"""One side's read-only identity, clock, material and authoritative quest score."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


def format_seconds(seconds: int) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class PlayerView(ttk.Frame):
    """Display exactly one participant's detached state; no duplicated owner."""

    def __init__(self, master: tk.Misc, side: int) -> None:
        super().__init__(master, padding=(5, 7))
        if side not in (-1, 1):
            raise ValueError("participant side must be -1 or 1")
        self.side = side
        self.name = tk.StringVar()
        self.clock = tk.StringVar(value="00:00")
        self.captured = tk.StringVar(value="Taken: —")
        self.lost = tk.StringVar(value="Lost: —")
        self.score = tk.StringVar(value="Score: 0")
        self.turn = tk.StringVar()
        self.columnconfigure(0, weight=1)
        ttk.Label(
            self,
            textvariable=self.name,
            font=("TkDefaultFont", 11, "bold"),
            wraplength=164,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(self, textvariable=self.clock, font=("TkDefaultFont", 19, "bold")).grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )
        ttk.Label(self, textvariable=self.turn, font=("TkDefaultFont", 9)).grid(
            row=2, column=0, sticky="w"
        )
        for row, value in enumerate((self.captured, self.lost, self.score), start=3):
            ttk.Label(self, textvariable=value, wraplength=160).grid(
                row=row, column=0, sticky="w", pady=(3, 0)
            )

    def refresh(self, state: dict[str, Any], remaining_ms: dict[str, int]) -> None:
        side_key = str(self.side)
        participant = state["participants"][side_key]
        color = "White" if self.side == 1 else "Black"
        self.name.set(f"{color} · {participant}")
        self.clock.set(format_seconds((remaining_ms[side_key] + 999) // 1000))
        if state["outcome"] is not None:
            self.turn.set("Finished")
        else:
            self.turn.set("● To move" if state["active_side"] == self.side else "Waiting")
        taken = [entry["kind"] for entry in state["captured"] if entry["side"] == -self.side]
        lost = [entry["kind"] for entry in state["captured"] if entry["side"] == self.side]
        self.captured.set("Taken: " + ", ".join(taken) if taken else "Taken: —")
        self.lost.set("Lost: " + ", ".join(lost) if lost else "Lost: —")
        self.score.set(f"Quest score: {state['quest_scores'][participant]}")
