"""Participant-owned, definition-driven quest cards and their live progress."""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable


class QuestCard(ttk.Frame):
    """A complete configured quest; display values never control game rules."""

    def __init__(
        self,
        master: tk.Misc,
        name: str,
        progress: dict[str, Any],
        *,
        description: str,
        reward: int,
    ) -> None:
        super().__init__(master, padding=(7, 7), borderwidth=1, relief="groove")
        style = ttk.Style(self)
        style.configure("QuestActive.TLabel", foreground="#285e8e")
        style.configure("QuestComplete.TLabel", foreground="#247344")
        self.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(
            self, text=name, font=("TkDefaultFont", 9, "bold"), wraplength=120
        )
        self.title_label.grid(row=0, column=0, sticky="ew")
        self.description_label = ttk.Label(self, text=description, wraplength=120)
        self.description_label.grid(row=1, column=0, sticky="ew", pady=(3, 5))
        self.progress_label = ttk.Label(self, wraplength=120)
        self.progress_label.grid(row=2, column=0, sticky="ew")
        self.indicator = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.indicator.grid(row=3, column=0, sticky="ew", pady=(3, 4))
        self.reward_label = ttk.Label(self, text=f"Reward: {reward} pts")
        self.reward_label.grid(row=4, column=0, sticky="ew")
        self.bind("<Configure>", self._resize_text)
        self.update_progress(progress)

    def _resize_text(self, event: tk.Event) -> None:
        width = max(80, event.width - 20)
        for widget in (self.title_label, self.description_label, self.progress_label):
            widget.configure(wraplength=width)

    def update_progress(self, progress: dict[str, Any]) -> None:
        current = progress["active"]
        target = progress["target"]
        completed = bool(progress["completed"])
        self.progress_label.configure(
            text=f"{current}/{target} · {'Completed' if completed else 'In progress'}",
            style="QuestComplete.TLabel" if completed else "QuestActive.TLabel",
        )
        self.indicator.configure(
            maximum=max(1, target), value=target if completed else min(current, target)
        )


class QuestList(ttk.Frame):
    """Render every quest for this side, with independently scrollable parent."""

    def __init__(self, master: tk.Misc, side: int, viewport: tk.Canvas | None = None) -> None:
        super().__init__(master, padding=(2, 3))
        if side not in (-1, 1):
            raise ValueError("quest side must be -1 or 1")
        self.side = side
        self.viewport = viewport
        self._definition_key: tuple[Any, ...] | None = None
        self._last: tuple[Any, ...] | None = None
        self.cards: list[QuestCard] = []
        self._card_ids: list[str] = []

    def _scroll(self, event: tk.Event) -> str:
        if self.viewport is not None:
            if getattr(event, "num", None) in (4, 5):
                amount = -3 if event.num == 4 else 3
            else:
                delta = getattr(event, "delta", 0)
                amount = (-1 if delta > 0 else 1) * max(1, abs(delta) // 120)
            self.viewport.yview_scroll(amount, "units")
        return "break"

    def _attach_scrolling(self, widget: tk.Misc) -> None:
        if self.viewport is None:
            return
        widget.bind("<MouseWheel>", self._scroll)
        widget.bind("<Button-4>", self._scroll)
        widget.bind("<Button-5>", self._scroll)
        widget.bind("<Button-1>", lambda _event: self.viewport.focus_set())
        for child in widget.winfo_children():
            self._attach_scrolling(child)

    def refresh(self, state: dict[str, Any]) -> None:
        participant = state["participants"][str(self.side)]
        records = state["quest_progress"][participant]
        definitions = state["config"]["quests"]
        # A new session, different participant or even an in-place changed
        # definition invalidates rendered content, irrespective of matching IDs.
        definition_key = (
            state["game_id"],
            state["config"].get("name"),
            participant,
            json.dumps(definitions, sort_keys=True),
        )
        progress_key = tuple(
            (
                quest["id"],
                records[quest["id"]]["active"],
                records[quest["id"]]["target"],
                records[quest["id"]]["completed"],
            )
            for quest in definitions
        )
        if definition_key == self._definition_key and progress_key == self._last:
            return
        if definition_key != self._definition_key:
            self._definition_key = definition_key
            for child in self.winfo_children():
                child.destroy()
            self.cards.clear()
            self._card_ids.clear()
            if not definitions:
                empty = ttk.Label(self, text="No quests configured for this game.")
                empty.pack(anchor="w", padx=5, pady=6)
                self._attach_scrolling(empty)
            for quest in definitions:
                quest_id = quest["id"]
                card = QuestCard(
                    self,
                    quest.get("title") or quest_id.replace("-", " ").replace("_", " ").title(),
                    records[quest_id],
                    description=quest["description"],
                    reward=quest["reward"],
                )
                card.pack(fill="x", pady=(0, 7))
                self.cards.append(card)
                self._card_ids.append(quest_id)
                self._attach_scrolling(card)
            if self.viewport is not None:
                self.viewport.yview_moveto(0.0)
        else:
            # Keep widgets and scroll position during frequent clock/progress refreshes.
            for quest_id, card in zip(self._card_ids, self.cards):
                card.update_progress(records[quest_id])
        self._last = progress_key
