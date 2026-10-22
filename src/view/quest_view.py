"""Player-visible quest cards rendered from authoritative JSON progress."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


class QuestCard(ttk.Frame):
    """Display one immutable definition and participant's earned progress."""

    def __init__(
        self, master: tk.Misc, name: str, progress: dict[str, Any],
        *, description: str, reward: int,
    ) -> None:
        super().__init__(master, padding=(8, 4))
        ttk.Label(self, text=name, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        ttk.Label(self, text=description, wraplength=240).pack(anchor="w")
        current = progress.get("active", 0)
        target = progress.get("target", 1)
        completed = progress.get("completed", False)
        ttk.Label(
            self,
            text=f"{current}/{target} · {'Complete' if completed else 'Active'} · {reward} pts",
        ).pack(anchor="w")


class QuestList(ttk.Frame):
    """Display the durable game-owned quest ledger without executable handlers."""

    def __init__(self, master: tk.Misc, limit: int = 6) -> None:
        super().__init__(master, padding=(8, 4))
        self.limit = limit
        self._last: tuple[Any, ...] | None = None
        self.cards: list[QuestCard] = []

    def refresh(self, state: dict[str, Any]) -> None:
        progress = state.get("quest_progress", {})
        definitions = {item["id"]: item for item in state["config"]["quests"]}
        rows = tuple(
            (player, quest_id, record.get("active"), record.get("target"), record.get("completed"))
            for player, quests in sorted(progress.items())
            for quest_id, record in sorted(quests.items())
        )[: self.limit]
        if rows == self._last:
            return
        self._last = rows
        for card in self.cards:
            card.destroy()
        self.cards = []
        for child in self.winfo_children():
            child.destroy()
        if not rows:
            ttk.Label(self, text="No active quests.").pack(anchor="w")
            return
        for player, name, active, target, completed in rows:
            definition = definitions[name]
            card = QuestCard(
                self, f"{player}: {name}",
                {"active": active, "target": target, "completed": completed},
                description=definition["description"], reward=definition["reward"],
            )
            card.pack(fill="x", pady=2)
            self.cards.append(card)
