"""src/model/manager.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations

class VysledekAkce:
    """TODO: implement this contract."""

    pass


class GameManager:
    """TODO: implement this contract."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    @property
    def aktivni_hrac(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def mozne_tahy(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def proved_akci(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def zkus_ulozit(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def reset(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
