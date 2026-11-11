"""Reusable player identity, score and six quest states."""

import tkinter as tk
from model.manager import GameManager

BG = "#f4f4f1"
INK = "#22262d"
MUTED = "#626a76"


class HracGameView(tk.Frame):
    """Reusable side panel reading profile XP and match-local quest completion."""

    def __init__(self, parent, color: str):
        super().__init__(parent, bg=BG, highlightbackground="#dadce0", highlightthickness=1)
        self.barva = color
        self.title = tk.Label(self, font=("Arial", 14, "bold"), anchor="w", bg=BG, fg=INK)
        self.title.pack(fill="x", padx=14, pady=(14, 3))
        self.identity = tk.Label(self, font=("Arial", 10), anchor="w", bg=BG, fg=MUTED)
        self.identity.pack(fill="x", padx=14)
        self.xp = tk.Label(self, font=("Arial", 13, "bold"), anchor="w", bg=BG, fg=INK)
        self.xp.pack(fill="x", padx=14, pady=(10, 9))
        tk.Frame(self, height=1, bg="#dbdee3").pack(fill="x", padx=12)
        tk.Label(self, text="QUESTS", font=("Arial", 9, "bold"), anchor="w", bg=BG, fg=MUTED).pack(
            fill="x", padx=14, pady=(12, 6)
        )
        self.quests = []
        for _ in range(6):
            label = tk.Label(
                self,
                font=("Arial", 9),
                anchor="w",
                justify="left",
                bg=BG,
                fg=INK,
                wraplength=176,
            )
            label.pack(fill="x", padx=14, pady=3)
            self.quests.append(label)
        tk.Frame(self, height=1, bg="#dbdee3").pack(fill="x", padx=12, pady=8)
        self.captures = tk.Label(
            self,
            font=("Arial", 9),
            anchor="w",
            justify="left",
            bg=BG,
            fg=MUTED,
            wraplength=170,
        )
        self.captures.pack(fill="x", padx=14, pady=(0, 12))

    def zobraz_hrace(self, manager: GameManager) -> None:
        player = manager.hraci[self.barva]
        selected = manager.stav == "in_progress" and manager.aktivni_barva == self.barva
        self.config(
            highlightbackground="#3179a6" if selected else "#dadce0",
            highlightthickness=2 if selected else 1,
        )
        self.title.config(
            text=("●  " if selected else "") + self.barva.title() + " · " + player.uzivatel.jmeno
        )
        self.identity.config(text="@" + player.uzivatel.uzivatelske_jmeno)
        self.xp.config(text=f"{player.uzivatel.xp} XP")
        for label, quest in zip(self.quests, manager.quest_manager.quests):
            completed = manager.quest_manager.dokoncil(
                player.uzivatel.uzivatelske_jmeno, quest.rule_id
            )
            label.config(
                text=f"{'✓' if completed else '○'}  {quest.nazev}  ·  {quest.xp} XP",
                fg="#18694b" if completed else INK,
            )
        captured = (
            manager.plocha.vyhozene_figurky_b
            if self.barva == "black"
            else manager.plocha.vyhozene_figurky_c
        )
        self.captures.config(text="Captured: " + (" ".join(p.kod for p in captured) or "—"))

    def zobraz_questy(self, manager: GameManager) -> None:
        self.zobraz_hrace(manager)
