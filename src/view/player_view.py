"""Read-only player panel over detached authoritative session state."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


def format_seconds(seconds: int) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class PlayerView(ttk.Frame):
    """Show participant identity, authoritative time and captured material."""

    def __init__(self, master: tk.Misc, side: int) -> None:
        super().__init__(master, padding=(10, 6))
        if side not in (-1, 1):
            raise ValueError("participant side must be -1 or 1")
        self.side = side
        self.name = tk.StringVar(value="White" if side == 1 else "Black")
        self.clock = tk.StringVar(value=format_seconds(0))
        self.captured = tk.StringVar(value="Taken:")
        self.lost = tk.StringVar(value="Lost:")
        # Compact panels preserve both clocks without consuming four rows per player.
        self.columnconfigure(1, weight=1)
        ttk.Label(self, textvariable=self.name, font=("TkDefaultFont", 13, "bold")).grid(
            row=0, column=0, sticky="w", padx=(0, 12)
        )
        ttk.Label(self, textvariable=self.clock, font=("TkDefaultFont", 16)).grid(
            row=0, column=1, sticky="e"
        )
        ttk.Label(self, textvariable=self.captured, wraplength=210).grid(
            row=1, column=0, sticky="nw", padx=(0, 12)
        )
        ttk.Label(self, textvariable=self.lost, wraplength=210).grid(
            row=1, column=1, sticky="ne"
        )

    def refresh(self, state: dict[str, Any], remaining_ms: dict[str, int]) -> None:
        participant = state["participants"][str(self.side)]
        self.name.set(f"{'White' if self.side == 1 else 'Black'} · {participant}")
        self.clock.set(format_seconds((remaining_ms[str(self.side)] + 999) // 1000))
        taken = [entry["kind"] for entry in state["captured"] if entry["side"] == -self.side]
        lost = [entry["kind"] for entry in state["captured"] if entry["side"] == self.side]
        self.captured.set("Taken: " + ", ".join(taken) if taken else "Taken:")
        self.lost.set("Lost: " + ", ".join(lost) if lost else "Lost:")
