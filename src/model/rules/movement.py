"""Ordinary move candidate generation, ownership and king-safety guards."""
from model.board import uvnitr
from model.move import Tah
from model.piece import Kral, Kun, Pesak
from model.rules.base import Rule, RuleContext


class TurnOwnershipRule(Rule):
    id = "turn_ownership"
    nazev = "Turn ownership"

    def povoleno(self, context: RuleContext) -> bool:
        if context.stav != "in_progress":
            return False
        if context.akce.typ == "resign":
            return True
        if context.tah is None:
            return False
        piece = context.pred.vrat_obsah(context.tah.odkud)
        return piece is not None and piece.barva == context.puvodni_hrac.barva


class BasicMovementRule(Rule):
    id = "basic_movement"
    nazev = "Ordinary movement"

    def kandidati(self, context: RuleContext) -> tuple[Tah, ...]:
        if context.vychozi_pole is None:
            return ()
        s = context.vychozi_pole
        board = context.pred
        piece = board.vrat_obsah(s)
        if piece is None or piece.barva != context.puvodni_hrac.barva:
            return ()
        r,c = s
        moves = []
        if isinstance(piece, Pesak):
            d = -1 if piece.barva == "white" else 1
            near = (r+d,c)
            if uvnitr(near) and board.vrat_obsah(near) is None:
                if near[0] not in (0,7):
                    moves.append(Tah(s, near, "normal"))
                far = (r+2*d,c)
                if r == (6 if d == -1 else 1) and not piece.pohnuta and board.vrat_obsah(far) is None:
                    moves.append(Tah(s, far, "pawn_double"))
            for dx in (-1,1):
                end = (r+d,c+dx)
                if not uvnitr(end):
                    continue
                victim = board.vrat_obsah(end)
                if victim and victim.barva != piece.barva and end[0] not in (0,7):
                    moves.append(Tah(s,end,"capture"))
            return tuple(moves)
        for dr,dc in piece.vektory:
            step = 1
            while True:
                dst = (r+dr*step,c+dc*step)
                if not uvnitr(dst):
                    break
                victim = board.vrat_obsah(dst)
                if victim is None:
                    moves.append(Tah(s,dst,"normal"))
                elif victim.barva != piece.barva:
                    moves.append(Tah(s,dst,"capture"))
                    break
                else:
                    break
                if isinstance(piece, (Kun,Kral)):
                    break
                step += 1
        return tuple(moves)


class KingCaptureRule(Rule):
    id = "king_capture"
    nazev = "King capture prevention"

    def povoleno(self, context: RuleContext) -> bool:
        return context.tah is None or not isinstance(context.pred.vrat_obsah(context.tah.kam), Kral)


class KingSafetyRule(Rule):
    id = "king_safety"
    nazev = "King safety"

    def povoleno(self, context: RuleContext) -> bool:
        if context.po is None or context.ohrozene is None:
            return True
        king = context.po.kral(context.puvodni_hrac.barva)
        other = "black" if context.puvodni_hrac.barva == "white" else "white"
        return king is not None and king not in context.ohrozene(context.po,other)
