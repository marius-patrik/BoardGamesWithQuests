"""src/model/move.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations

class Tah:
    """TODO: implement this contract."""

    def __post_init__(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

class Akce:
    """TODO: implement this contract."""

    @classmethod
    def move(cls, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    @classmethod
    def resign(cls, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
