"""src/view/panel.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations

import tkinter as tk


class HracGameView(tk.Frame):
    """TODO: implement this contract."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def zobraz_hrace(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def zobraz_questy(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
