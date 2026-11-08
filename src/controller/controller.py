"""Ephemeral input selection, promotion selection and model action submission."""

from __future__ import annotations
from collections.abc import Callable
from model.board import Square
from model.move import Akce, Tah
from model.manager import GameManager, VysledekAkce
from model.validator import IllegalAction


class GameManagerController:
    def __init__(
        self, manager: GameManager, on_refresh: Callable[[], None] | None = None
    ) -> None:
        self.manager = manager
        self.on_refresh = on_refresh or (lambda: None)
        self.vybrane: Square | None = None
        self.destinace: tuple[Square, ...] = ()
        self.cekajici_promena: tuple[Tah, ...] = ()
        self.last_message = "White to move"

    def _refresh(self) -> None:
        self.on_refresh()

    def zrus_vyber(self) -> None:
        self.vybrane = None
        self.destinace = ()
        self.cekajici_promena = ()
        self._refresh()

    def vyber_pole(self, square: Square) -> tuple[Tah, ...]:
        """Returns promotion alternatives only when the user must choose one."""
        self.cekajici_promena = ()
        if self.manager.stav != "in_progress":
            self.last_message = "The game is over. Start a new match."
            self._refresh()
            return ()
        piece = self.manager.plocha.vrat_obsah(square)
        if square == self.vybrane:
            self.zrus_vyber()
            return ()
        if piece and piece.barva == self.manager.aktivni_barva:
            self.vybrane = square
            self.destinace = tuple(
                dict.fromkeys(m.kam for m in self.manager.mozne_tahy(square))
            )
            self.last_message = (
                f"{piece.nazev} selected · {len(self.destinace)} legal destinations"
            )
            self._refresh()
            return ()
        if self.vybrane is None:
            self.last_message = "Select a piece of the active player"
            self._refresh()
            return ()
        available = tuple(
            m for m in self.manager.mozne_tahy(self.vybrane) if m.kam == square
        )
        if not available:
            self.last_message = "Illegal destination; choose a highlighted square"
            self._refresh()
            return ()
        if len(available) > 1 and all(m.promena for m in available):
            self.cekajici_promena = available
            self.last_message = "Choose the promotion piece"
            self._refresh()
            return available
        self._submit(Akce.move(available[0]))
        return ()

    def potvrd_promenu(self, code: str) -> VysledekAkce | None:
        if not self.cekajici_promena:
            return None
        option = next(
            (move for move in self.cekajici_promena if move.promena == code), None
        )
        if option is None:
            raise ValueError("Choose Q, R, B or N")
        return self._submit(Akce.move(option))

    def _submit(self, akce: Akce) -> VysledekAkce | None:
        try:
            result = self.manager.proved_akci(akce)
        except IllegalAction as exc:
            self.last_message = str(exc)
            self._refresh()
            return None
        self.vybrane = None
        self.destinace = ()
        self.cekajici_promena = ()
        self.last_message = result.text
        if result.xp_awarded:
            self.last_message += f" · +{result.xp_awarded} XP ({', '.join(q.nazev for q in result.quests)})"
        self._refresh()
        return result

    def odstup(self) -> VysledekAkce | None:
        return self._submit(Akce.resign())

    def novou_hru(self) -> None:
        self.manager = self.manager.reset()
        self.vybrane = None
        self.destinace = ()
        self.cekajici_promena = ()
        self.last_message = "New match · White to move"
        self._refresh()
