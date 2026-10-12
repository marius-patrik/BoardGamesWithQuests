"""Minimal game window; the full game view arrives in the later stack."""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from engine.model.game.games import default_configuration_name


def build_application(root: tk.Tk, game: Optional[str] = None) -> tk.Tk:
    """Show the configured game's application shell."""
    selection = game or default_configuration_name()
    if not selection:
        raise ValueError("no playable game package installed")
    root.title(f"ChessWithQuests - {selection}")
    style = ttk.Style(root)
    style.theme_use(style.theme_names()[0])
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="ChessWithQuests", font=("TkDefaultFont", 20)).pack(pady=(0, 8))
    ttk.Label(frame, text=f"Configuration: {selection}").pack(pady=(0, 8))
    ttk.Label(frame, text="The game view arrives in the view layer.").pack()
    return root
