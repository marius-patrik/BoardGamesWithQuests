"""Player-visible quest cards rendered from authoritative JSON progress."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


class QuestCard(ttk.Frame):
    """Read-only reward and progress for one declared quest and participant."""

    def __init__(self, master: tk.Misc, name: str, progress: dict[str, Any]) -> None:
        super().__init__(master, padding=(8, 4))
        ttk.Label(self, text=name, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        current = progress.get("active", 0)
        target = progress.get("target", 1)
        completed = progress.get("completed", False)
        ttk.Label(self, text=f"{current}/{target} · {'Complete' if completed else 'Active'}").pack(
            anchor="w"
        )


class QuestList(ttk.Frame):
    """Display active quests without invoking executable quest classes."""

    def __init__(self, master: tk.Misc, limit: int = 6) -> None:
        super().__init__(master, padding=(8, 4))
        self.limit = limit
        self._last: tuple[Any, ...] | None = None
        self.cards: list[QuestCard] = []

    def refresh(self, state: dict[str, Any]) -> None:
        progress = state.get("quest_progress", {})
        rows = tuple(
            (player, quest_id, record.get("active"), record.get("target"),
             record.get("completed"))
            for player, quests in sorted(progress.items())
            for quest_id, record in sorted(quests.items())
        )[: self.limit]
        if rows == self._last:
            return
        self._last = rows
        for card in self.cards:
            card.destroy()
        self.cards = []
        if not rows:
            ttk.Label(self, text="No active quests.").pack(anchor="w")
            return
        for player, name, active, target, completed in rows:
            card = QuestCard(self, f"{player}: {name}", {
                "active": active, "target": target, "completed": completed
            })
            card.pack(fill="x", pady=2)
            self.cards.append(card)
