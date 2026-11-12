"""src/model/validator.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations

class IllegalAction(ValueError):
    """TODO: implement this contract."""

    pass


class PripravenyTah:
    """TODO: implement this contract."""

    pass


class RevizorTahu:
    """TODO: implement this contract."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def ohrozena_pole(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def v_sachu(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def _context(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def _candidates(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def _castle_safe_transit(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def _stage(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def mozne_tahy(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def vyhodnot(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
