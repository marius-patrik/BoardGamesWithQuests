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
    """Facts for one request: pred is committed input, po is disposable output.

    Rule hooks may change only the staged board through po, never pred. Their
    output is evaluated before GameManager publishes a new authoritative board.
    """

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
    """Stateless, ordered Chess rule with four noninterchangeable hook phases.

    Candidate hooks propose moves; guard hooks reject; supplement hooks stage
    special effects; observation hooks report events for terminal/quest logic.
    """

    id = "rule"
    nazev = "Rule"
    popis = ""
    quest_xp = 0

    def kandidati(self, context: RuleContext) -> tuple[Tah, ...]:
        """Propose full move identities without committing changes."""
        return ()

    def povoleno(self, context: RuleContext) -> bool:
        """Return False only when this rule forbids the requested action."""
        return True

    def priprav(self, context: RuleContext) -> Figurka | None:
        """Mutate context.po for one special effect; return an extra victim, if any."""
        return None

    def nastalo(self, context: RuleContext) -> bool:
        """Report an observed event; False means absent, not an illegal move."""
        return False
