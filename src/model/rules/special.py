"""Castling, en-passant and promotion candidate generation and staged effects."""

from model.board import uvnitr
from model.move import Tah
from model.piece import Kral, Pesak, Vez
from model.rules.base import Rule, RuleContext


class CastlingRule(Rule):
    id = "castling"
    nazev = "Castling"
    popis = "Complete a legal castle"
    quest_xp = 15

    def kandidati(self, context: RuleContext) -> tuple[Tah, ...]:
        if context.vychozi_pole is None or context.ohrozene is None:
            return ()
        board = context.pred
        source = context.vychozi_pole
        king = board.vrat_obsah(source)
        if (
            not isinstance(king, Kral)
            or king.pohnuta
            or king.barva != context.puvodni_hrac.barva
        ):
            return ()
        home = 7 if king.barva == "white" else 0
        if source != (home, 4):
            return ()
        opponent = "black" if king.barva == "white" else "white"
        attacks = context.ohrozene(board, opponent)
        if source in attacks:
            return ()
        result = []
        for rook_col, transit_col, dest_col, between, kind in (
            (7, 5, 6, (5, 6), "castle_kingside"),
            (0, 3, 2, (1, 2, 3), "castle_queenside"),
        ):
            rook = board.vrat_obsah((home, rook_col))
            if not isinstance(rook, Vez) or rook.barva != king.barva or rook.pohnuta:
                continue
            if any(board.vrat_obsah((home, c)) is not None for c in between):
                continue
            if (home, transit_col) in attacks or (home, dest_col) in attacks:
                continue
            result.append(Tah(source, (home, dest_col), kind))
        return tuple(result)

    def priprav(self, context: RuleContext):
        if (
            context.po is not None
            and context.tah is not None
            and context.tah.typ_tahu.startswith("castle_")
        ):
            row = context.tah.odkud[0]
            if context.tah.typ_tahu == "castle_kingside":
                context.po.presun((row, 7), (row, 5))
            else:
                context.po.presun((row, 0), (row, 3))
        return None

    def nastalo(self, context: RuleContext) -> bool:
        return context.tah is not None and context.tah.typ_tahu.startswith("castle_")


class EnPassantRule(Rule):
    id = "en_passant"
    nazev = "En passant"
    popis = "Capture a pawn en passant"
    quest_xp = 20

    def kandidati(self, context: RuleContext) -> tuple[Tah, ...]:
        prev = context.predchozi_tah
        if (
            context.vychozi_pole is None
            or prev is None
            or prev.typ_tahu != "pawn_double"
        ):
            return ()
        src = context.vychozi_pole
        pawn = context.pred.vrat_obsah(src)
        victim = context.pred.vrat_obsah(prev.kam)
        if not isinstance(pawn, Pesak) or pawn.barva != context.puvodni_hrac.barva:
            return ()
        if not isinstance(victim, Pesak) or victim.barva == pawn.barva:
            return ()
        if src[0] != prev.kam[0] or abs(src[1] - prev.kam[1]) != 1:
            return ()
        d = -1 if pawn.barva == "white" else 1
        end = (src[0] + d, prev.kam[1])
        if not uvnitr(end) or context.pred.vrat_obsah(end) is not None:
            return ()
        return (Tah(src, end, "en_passant"),)

    def priprav(self, context: RuleContext):
        if (
            context.po is not None
            and context.tah is not None
            and context.tah.typ_tahu == "en_passant"
        ):
            src = context.tah.odkud
            victim = context.po.odstran((src[0], context.tah.kam[1]))
            if not isinstance(victim, Pesak):
                raise ValueError("En passant victim missing")
            return victim
        return None

    def nastalo(self, context: RuleContext) -> bool:
        return context.tah is not None and context.tah.typ_tahu == "en_passant"


class PromotionRule(Rule):
    id = "promotion"
    nazev = "Promotion"
    popis = "Promote a pawn"
    quest_xp = 25

    def kandidati(self, context: RuleContext) -> tuple[Tah, ...]:
        if context.vychozi_pole is None:
            return ()
        s = context.vychozi_pole
        board = context.pred
        pawn = board.vrat_obsah(s)
        if not isinstance(pawn, Pesak) or pawn.barva != context.puvodni_hrac.barva:
            return ()
        d = -1 if pawn.barva == "white" else 1
        row = s[0] + d
        if row not in (0, 7):
            return ()
        possibilities = []
        forward = (row, s[1])
        if board.vrat_obsah(forward) is None:
            possibilities.append((forward, "promotion"))
        for dc in (-1, 1):
            dst = (row, s[1] + dc)
            victim = board.vrat_obsah(dst)
            if uvnitr(dst) and victim is not None and victim.barva != pawn.barva:
                possibilities.append((dst, "promotion_capture"))
        return tuple(
            Tah(s, dst, kind, choice)
            for dst, kind in possibilities
            for choice in ("Q", "R", "B", "N")
        )

    def priprav(self, context: RuleContext):
        if (
            context.po is not None
            and context.tah is not None
            and context.tah.typ_tahu.startswith("promotion")
        ):
            assert context.tah.promena is not None
            context.po.promenu(context.tah.kam, context.tah.promena)
        return None

    def nastalo(self, context: RuleContext) -> bool:
        return context.tah is not None and context.tah.typ_tahu.startswith("promotion")
