"""Gameplay rule observed after a committed capture."""

from model.rules.base import Rule, RuleContext


class CaptureRule(Rule):
    id = "capture"
    nazev = "Capture"
    popis = "Capture an enemy piece"
    quest_xp = 10

    def nastalo(self, context: RuleContext) -> bool:
        return context.capture is not None
