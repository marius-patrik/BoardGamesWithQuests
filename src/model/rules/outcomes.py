"""src/model/rules/outcomes.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations

from .base import Rule


class CheckRule(Rule):
    """TODO: implement this contract."""

    def nastalo(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")


class CheckmateRule(Rule):
    """TODO: implement this contract."""

    def nastalo(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")


class StalemateRule(Rule):
    """TODO: implement this contract."""

    def nastalo(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")


class ResignationRule(Rule):
    """TODO: implement this contract."""

    def povoleno(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
