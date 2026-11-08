"""Pure legal-move evaluator: rule candidates -> guards -> staging -> observations."""

from __future__ import annotations
from dataclasses import dataclass, replace
from model.board import HerniPlocha, Square, uvnitr
from model.move import Akce, Tah
from model.piece import Kral, Kun, Pesak, Figurka
from model.player import Hrac
from model.rules.base import Rule, RuleContext
from model.rules.movement import (
    TurnOwnershipRule,
    BasicMovementRule,
    KingCaptureRule,
    KingSafetyRule,
)
from model.rules.special import CastlingRule, EnPassantRule, PromotionRule
from model.rules.outcomes import (
    CheckRule,
    CheckmateRule,
    StalemateRule,
    ResignationRule,
)
from model.rules.quests import CaptureRule


class IllegalAction(ValueError):
    """Rejected action never mutates committed board, turn, history or XP."""


@dataclass(frozen=True)
class PripravenyTah:
    plocha: HerniPlocha
    tah: Tah | None
    captured: Figurka | None
    matched_rule_ids: tuple[str, ...]
    reason: str | None = None
    winner: str | None = None


class RevizorTahu:
    def __init__(self) -> None:
        self.rules: tuple[Rule, ...] = (
            TurnOwnershipRule(),
            BasicMovementRule(),
            KingCaptureRule(),
            KingSafetyRule(),
            CastlingRule(),
            EnPassantRule(),
            PromotionRule(),
            CheckRule(),
            CheckmateRule(),
            StalemateRule(),
            ResignationRule(),
            CaptureRule(),
        )
        self.by_id = {rule.id: rule for rule in self.rules}

    def ohrozena_pole(self, board: HerniPlocha, color: str) -> set[Square]:
        """Geometric attacks, including pawn diagonals and attacks by pinned pieces."""
        attacked: set[Square] = set()
        for s, p in board.pole_figurek():
            if p.barva != color:
                continue
            r, c = s
            if isinstance(p, Pesak):
                d = -1 if p.barva == "white" else 1
                attacked.update(dst for dc in (-1, 1) if uvnitr(dst := (r + d, c + dc)))
                continue
            for dr, dc in p.vektory_utoku:
                distance = 1
                while True:
                    dst = (r + dr * distance, c + dc * distance)
                    if not uvnitr(dst):
                        break
                    attacked.add(dst)
                    if board.vrat_obsah(dst) or isinstance(p, (Kral, Kun)):
                        break
                    distance += 1
        return attacked

    def v_sachu(self, board: HerniPlocha, color: str) -> bool:
        king = board.kral(color)
        if king is None:
            return True
        other = "black" if color == "white" else "white"
        return king in self.ohrozena_pole(board, other)

    def _context(
        self,
        board: HerniPlocha,
        player: Hrac,
        action: Akce,
        last: Tah | None,
        state: str,
        source: Square | None = None,
    ) -> RuleContext:
        return RuleContext(
            action,
            action.tah,
            player,
            board,
            predchozi_tah=last,
            ohrozene=self.ohrozena_pole,
            stav=state,
            zdroj=source,
        )

    def _candidates(self, context: RuleContext) -> tuple[Tah, ...]:
        candidates: dict[Tah, None] = {}
        for rule in self.rules:
            for candidate in rule.kandidati(context):
                candidates[candidate] = None
        return tuple(candidates)

    def _castle_safe_transit(self, ctx: RuleContext) -> bool:
        move = ctx.tah
        if move is None or not move.typ_tahu.startswith("castle_"):
            return True
        # The king's initial occupancy may screen a sliding attack through its transit square.
        transit = (move.odkud[0], 5 if move.typ_tahu == "castle_kingside" else 3)
        temporary = ctx.pred.kopie()
        temporary.presun(move.odkud, transit)
        return not self.v_sachu(temporary, ctx.puvodni_hrac.barva)

    def _stage(self, context: RuleContext) -> tuple[RuleContext, HerniPlocha] | None:
        if context.tah is None:
            return None
        if not all(
            r.povoleno(context)
            for r in self.rules
            if isinstance(r, (TurnOwnershipRule, KingCaptureRule))
        ):
            return None
        if not self._castle_safe_transit(context):
            return None
        board = context.pred.kopie()
        try:
            capture = board.presun(context.tah.odkud, context.tah.kam)
            staged = replace(context, po=board, capture=capture)
            for rule in self.rules:
                extra = rule.priprav(staged)
                if extra is not None:
                    if capture is not None:
                        raise ValueError("Two captures in one move")
                    capture = extra
                    staged = replace(staged, capture=capture)
        except (ValueError, AssertionError):
            return None
        safety = self.by_id["king_safety"]
        if not safety.povoleno(staged):
            return None
        return staged, board

    def mozne_tahy(
        self,
        board: HerniPlocha,
        player: Hrac,
        last: Tah | None = None,
        state: str = "in_progress",
        start: Square | None = None,
    ) -> tuple[Tah, ...]:
        if state != "in_progress":
            return ()
        if board.kral(player.barva) is None:
            return ()
        result: list[Tah] = []
        squares = (
            (start,)
            if start is not None
            else tuple(s for s, p in board.pole_figurek() if p.barva == player.barva)
        )
        for s in squares:
            if not uvnitr(s):
                continue
            p = board.vrat_obsah(s)
            if p is None or p.barva != player.barva:
                continue
            seed = self._context(board, player, Akce("inspect"), last, state, source=s)
            for candidate in self._candidates(seed):
                ctx = self._context(board, player, Akce.move(candidate), last, state)
                if self._stage(ctx) is not None:
                    result.append(candidate)
        return tuple(result)

    def vyhodnot(
        self,
        board: HerniPlocha,
        actor: Hrac,
        akce: Akce,
        last: Tah | None,
        state: str = "in_progress",
    ) -> PripravenyTah:
        if state != "in_progress":
            raise IllegalAction("The match has already finished")
        if akce.typ == "resign":
            ctx = self._context(board, actor, akce, last, state)
            if not self.by_id["resignation"].povoleno(ctx):
                raise IllegalAction("Invalid resignation")
            return PripravenyTah(
                board.kopie(),
                None,
                None,
                (),
                "resignation",
                "black" if actor.barva == "white" else "white",
            )
        if akce.typ != "move" or akce.tah is None:
            raise IllegalAction("Unknown action")
        source = akce.tah.odkud
        piece = board.vrat_obsah(source)
        if piece is None or piece.barva != actor.barva:
            raise IllegalAction("Select one of your own pieces")
        seed = self._context(board, actor, akce, last, state)
        if akce.tah not in self._candidates(seed):
            raise IllegalAction("This move is not legal for the selected piece")
        prepared = self._stage(seed)
        if prepared is None:
            raise IllegalAction(
                "Move would leave your king in check or violates the rules"
            )
        staged, after = prepared
        opponent = "black" if actor.barva == "white" else "white"
        checked = self.v_sachu(after, opponent)
        opponent_player = Hrac(
            opponent, actor.uzivatel
        )  # only color is examined in a legal-reply query
        reply = bool(self.mozne_tahy(after, opponent_player, akce.tah))
        observed = replace(staged, v_sachu=checked, ma_odpoved=reply)
        matches = tuple(rule.id for rule in self.rules if rule.nastalo(observed))
        reason = (
            "checkmate"
            if "checkmate" in matches
            else "stalemate" if "stalemate" in matches else None
        )
        winner = actor.barva if reason == "checkmate" else None
        return PripravenyTah(after, akce.tah, staged.capture, matches, reason, winner)
