"""Single authoritative Chess game state and one-commit action lifecycle."""
from __future__ import annotations
from dataclasses import dataclass
from model.board import HerniPlocha, algebraicky
from model.move import Tah, Akce
from model.player import Hrac
from model.user import UserManager
from model.validator import RevizorTahu, IllegalAction
from model.quest import QuestManager, Quest
from model.logger import GameLogger


@dataclass(frozen=True)
class VysledekAkce:
    tah: Tah | None
    matched_rule_ids: tuple[str, ...]
    xp_awarded: int
    quests: tuple[Quest, ...]
    reason: str | None
    winner: str | None
    text: str


class GameManager:
    def __init__(self, users: UserManager, white: str, black: str) -> None:
        if white == black or white not in users.uzivatele or black not in users.uzivatele:
            raise ValueError("Select two distinct existing profiles")
        self.users = users
        self.hraci = {"white":Hrac("white",users.uzivatele[white]),"black":Hrac("black",users.uzivatele[black])}
        self.plocha = HerniPlocha()
        self.aktivni_barva = "white"
        self.stav = "in_progress"
        self.reason: str | None = None
        self.winner: str | None = None
        self.revision = 0
        self.revizor = RevizorTahu()
        self.quest_manager = QuestManager(self.revizor.rules)
        self.logger = GameLogger(white,black,users.root)
        self.logger.uloz_historii()

    @property
    def aktivni_hrac(self) -> Hrac:
        return self.hraci[self.aktivni_barva]

    def mozne_tahy(self, start=None):
        return self.revizor.mozne_tahy(self.plocha,self.aktivni_hrac,self.logger.predchozi_tah,self.stav,start)

    def proved_akci(self, akce: Akce) -> VysledekAkce:
        actor = self.aktivni_hrac
        prepared = self.revizor.vyhodnot(self.plocha,actor,akce,self.logger.predchozi_tah,self.stav)
        # All validation and analysis completed before changing authoritative state.
        self.plocha = prepared.plocha
        self.revision += 1
        self.reason = prepared.reason
        self.winner = prepared.winner
        self.stav = "terminal" if prepared.reason else "in_progress"
        if akce.typ == "resign":
            message = f"{self.hraci[prepared.winner].uzivatel.jmeno} wins by resignation"
            self.logger.zaznamenej({"type":"resignation","actor":actor.uzivatel.uzivatelske_jmeno,"matched_rule_ids":[],"xp_awarded":0},self.reason,self.winner)
            gained,quests = 0,()
        else:
            assert prepared.tah is not None
            gained,quests = self.quest_manager.pridej_odmeny(prepared.matched_rule_ids,actor)
            if gained:
                self.users.pridej_xp(actor.uzivatel.uzivatelske_jmeno,gained)
            move = prepared.tah
            message = algebraicky(move.odkud) + (" × " if prepared.captured else " → ") + algebraicky(move.kam)
            if move.promena:
                message += "="+move.promena
            if self.reason == "checkmate":
                message += "# · Checkmate"
            elif self.reason == "stalemate":
                message += " · Stalemate"
            elif "check" in prepared.matched_rule_ids:
                message += "+ · Check"
            self.logger.zaznamenej({
                "type":"move","actor":actor.uzivatel.uzivatelske_jmeno,
                "from":list(move.odkud),"to":list(move.kam),"move_kind":move.typ_tahu,
                "promotion":move.promena,
                "capture":({"piece":prepared.captured.kod,"color":prepared.captured.barva} if prepared.captured else None),
                "matched_rule_ids":list(prepared.matched_rule_ids),"xp_awarded":gained,
            },self.reason,self.winner)
        if self.stav == "in_progress":
            self.aktivni_barva = "black" if actor.barva == "white" else "white"
        if gained:
            self.users.uloz_uzivatele()
        self.logger.uloz_historii()
        return VysledekAkce(prepared.tah,prepared.matched_rule_ids,gained,quests,self.reason,self.winner,message)

    def zkus_ulozit(self) -> tuple[bool,bool]:
        return self.users.uloz_uzivatele(),self.logger.uloz_historii()

    def reset(self) -> GameManager:
        return GameManager(self.users,self.hraci["white"].uzivatel.uzivatelske_jmeno,self.hraci["black"].uzivatel.uzivatelske_jmeno)
