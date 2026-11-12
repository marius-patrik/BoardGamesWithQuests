"""src/view/game.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations

import tkinter as tk

class GameView(tk.Frame):
    """TODO: implement this contract."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    @staticmethod
    def _activate(*args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def _focus(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def vykresli_desku(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def zvyrazni_tahy(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
