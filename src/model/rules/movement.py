"""src/model/rules/movement.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations

from .base import Rule


class TurnOwnershipRule(Rule):
    """TODO: implement this contract."""

    def povoleno(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")


class BasicMovementRule(Rule):
    """TODO: implement this contract."""

    def kandidati(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")


class KingCaptureRule(Rule):
    """TODO: implement this contract."""

    def povoleno(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")


class KingSafetyRule(Rule):
    """TODO: implement this contract."""

    def povoleno(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
