"""Post-move terminal/check observations; no recursive rule evaluation."""
from model.rules.base import Rule, RuleContext


class CheckRule(Rule):
    id = "check"
    nazev = "Check"
    popis = "Give check to the opponent's king"
    quest_xp = 10

    def nastalo(self, context: RuleContext) -> bool:
        return bool(context.v_sachu)


class CheckmateRule(Rule):
    id = "checkmate"
    nazev = "Checkmate"
    popis = "Deliver checkmate"
    quest_xp = 50

    def nastalo(self, context: RuleContext) -> bool:
        return context.v_sachu and not context.ma_odpoved


class StalemateRule(Rule):
    id = "stalemate"
    nazev = "Stalemate"

    def nastalo(self, context: RuleContext) -> bool:
        return not context.v_sachu and not context.ma_odpoved


class ResignationRule(Rule):
    id = "resignation"
    nazev = "Resignation"

    def povoleno(self, context: RuleContext) -> bool:
        return context.stav == "in_progress" and context.akce.typ == "resign" and context.akce.tah is None


