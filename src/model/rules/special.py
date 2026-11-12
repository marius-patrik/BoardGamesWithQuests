"""src/model/rules/special.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations

from .base import Rule

class CastlingRule(Rule):
    """TODO: implement this contract."""

    def kandidati(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def priprav(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def nastalo(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

class EnPassantRule(Rule):
    """TODO: implement this contract."""

    def kandidati(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def priprav(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def nastalo(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

class PromotionRule(Rule):
    """TODO: implement this contract."""

    def kandidati(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def priprav(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def nastalo(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
