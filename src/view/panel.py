"""One participant's identity, readable clock, material and quest score."""

from __future__ import annotations

from collections import Counter
import tkinter as tk
from tkinter import ttk
from typing import Any


def format_seconds(seconds: int) -> str:
    seconds = max(0, int(seconds))
    if seconds >= 3600:
        return f"{seconds // 3600:d}:{(seconds // 60) % 60:02d}:{seconds % 60:02d}"
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def material_summary(label: str, kinds: list[str]) -> str:
    if not kinds:
        return f"{label}: —"
    counts = Counter(kinds)
    items = ", ".join(
        f"{kind.replace('_', ' ')} ×{count}" if count > 1 else kind.replace("_", " ")
        for kind, count in sorted(counts.items())
    )
    return f"{label} ({len(kinds)}): {items}"


class PlayerView(ttk.Frame):
    """A detached projection of one player, never a second score/clock owner."""

    def __init__(self, master: tk.Misc, side: int) -> None:
        super().__init__(master, padding=(5, 6))
        if side not in (-1, 1):
            raise ValueError("participant side must be -1 or 1")
        self.side = side
        self.name = tk.StringVar()
        self.clock = tk.StringVar(value="00:00")
        self.captured = tk.StringVar(value="Taken: —")
        self.lost = tk.StringVar(value="Lost: —")
        self.score = tk.StringVar(value="Quest score: 0")
        self.turn = tk.StringVar()
        self.columnconfigure(0, weight=1)
        self.name_label = ttk.Label(
            self,
            textvariable=self.name,
            font=("TkDefaultFont", 11, "bold"),
            wraplength=150,
            justify="left",
        )
        self.name_label.grid(row=0, column=0, sticky="ew")
        self.clock_label = ttk.Label(
            self, textvariable=self.clock, font=("TkFixedFont", 18, "bold")
        )
        self.clock_label.grid(row=1, column=0, sticky="w", pady=(3, 0))
        style = ttk.Style(self)
        style.configure("CurrentPlayer.TLabel", foreground="#247344")
        style.configure("WaitingPlayer.TLabel", foreground="#555555")
        self.turn_label = ttk.Label(self, textvariable=self.turn, style="WaitingPlayer.TLabel")
        self.turn_label.grid(row=2, column=0, sticky="ew", pady=(1, 0))
        self.material_labels = []
        for row, value in enumerate((self.captured, self.lost, self.score), start=3):
            label = ttk.Label(self, textvariable=value, wraplength=150, justify="left")
            label.grid(row=row, column=0, sticky="ew", pady=(3, 0))
            self.material_labels.append(label)
        self.bind("<Configure>", self._resize_text)

    def _resize_text(self, event: tk.Event) -> None:
        width = max(80, event.width - 18)
        for label in (self.name_label, *self.material_labels):
            label.configure(wraplength=width)

    def refresh(self, state: dict[str, Any], remaining_ms: dict[str, int]) -> None:
        side_key = str(self.side)
        participant = str(state["participants"][side_key])
        color = "White" if self.side == 1 else "Black"
        self.name.set(
            color if participant.casefold() == color.casefold() else f"{color} · {participant}"
        )
        self.clock.set(format_seconds((remaining_ms[side_key] + 999) // 1000))
        finished = state["outcome"] is not None
        active = not finished and state["active_side"] == self.side
        self.turn.set("Game finished" if finished else "● To move" if active else "○ Waiting")
        self.turn_label.configure(
            style="CurrentPlayer.TLabel" if active else "WaitingPlayer.TLabel"
        )
        taken = [entry["kind"] for entry in state["captured"] if entry["side"] == -self.side]
        lost = [entry["kind"] for entry in state["captured"] if entry["side"] == self.side]
        self.captured.set(material_summary("Taken", taken))
        self.lost.set(material_summary("Lost", lost))
        self.score.set(f"Quest score: {state['quest_scores'][participant]}")
