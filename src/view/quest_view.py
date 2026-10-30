"""Player-owned quest cards from the authoritative participant progress ledger."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


class QuestCard(ttk.Frame):
    """Render one supported configured objective and its recorded progress."""

    def __init__(
        self,
        master: tk.Misc,
        name: str,
        progress: dict[str, Any],
        *,
        description: str,
        reward: int,
    ) -> None:
        super().__init__(master, padding=(3, 5))
        ttk.Label(self, text=name, font=("TkDefaultFont", 9, "bold"), wraplength=142).pack(
            anchor="w"
        )
        ttk.Label(self, text=description, wraplength=142).pack(anchor="w")
        current = progress.get("active", 0)
        target = progress.get("target", 1)
        completed = progress.get("completed", False)
        ttk.Label(
            self,
            text=f"{current}/{target} · {'Complete' if completed else 'Active'} · {reward} pts",
            wraplength=142,
        ).pack(anchor="w")


class QuestList(ttk.Frame):
    """Show all objectives belonging to one session participant (not both)."""

    def __init__(self, master: tk.Misc, side: int) -> None:
        super().__init__(master, padding=(2, 3))
        if side not in (-1, 1):
            raise ValueError("quest side must be -1 or 1")
        self.side = side
        self._last: tuple[Any, ...] | None = None
        self.cards: list[QuestCard] = []

    def refresh(self, state: dict[str, Any]) -> None:
        identity = state["participants"][str(self.side)]
        progress = state["quest_progress"][identity]
        definitions = {item["id"]: item for item in state["config"]["quests"]}
        rows = tuple(
            (
                quest_id,
                record["active"],
                record["target"],
                record["completed"],
                definitions[quest_id]["description"],
                definitions[quest_id]["reward"],
            )
            for quest_id, record in sorted(progress.items())
        )
        if rows == self._last:
            return
        self._last = rows
        for child in self.winfo_children():
            child.destroy()
        self.cards = []
        if not rows:
            ttk.Label(self, text="No quests for this player.").pack(anchor="w")
            return
        for name, active, target, completed, description, reward in rows:
            card = QuestCard(
                self,
                name.replace("-", " ").title(),
                {"active": active, "target": target, "completed": completed},
                description=description,
                reward=reward,
            )
            card.pack(fill="x", pady=2)
            self.cards.append(card)
