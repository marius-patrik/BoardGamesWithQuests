"""src/model/rules/base.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations


class RuleContext:
    """TODO: implement this contract."""

    @property
    def vychozi_pole(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")


class Rule:
    """TODO: implement this contract."""

    def kandidati(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def povoleno(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def priprav(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def nastalo(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")
