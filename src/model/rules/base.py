"""Rule protocol: candidate, permission, staged supplement and observation hooks."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from model.board import HerniPlocha, Square
from model.move import Akce, Tah
from model.piece import Figurka
from model.player import Hrac


@dataclass(frozen=True)
class RuleContext:
    akce: Akce
    tah: Tah | None
    puvodni_hrac: Hrac
    pred: HerniPlocha
    po: HerniPlocha | None = None
    predchozi_tah: Tah | None = None
    capture: Figurka | None = None
    v_sachu: bool = False
    ma_odpoved: bool = True
    ohrozene: Callable[[HerniPlocha, str], set[Square]] | None = None
    stav: str = "in_progress"
    zdroj: Square | None = None

    @property
    def vychozi_pole(self) -> Square | None:
        return self.tah.odkud if self.tah is not None else self.zdroj


class Rule:
    id = "rule"
    nazev = "Rule"
    popis = ""
    quest_xp = 0

    def kandidati(self, context: RuleContext) -> tuple[Tah, ...]:
        return ()

    def povoleno(self, context: RuleContext) -> bool:
        return True

    def priprav(self, context: RuleContext) -> Figurka | None:
        return None

    def nastalo(self, context: RuleContext) -> bool:
        return False
