"""Board storage and deterministic, disposable move effects."""
from __future__ import annotations

from dataclasses import replace
from model.piece import Figurka, Kral, Dama, Vez, Strelec, Kun, Pesak, PROMOTIONS

Square = tuple[int, int]


def uvnitr(s: Square) -> bool:
    return len(s) == 2 and all(type(v) is int and 0 <= v < 8 for v in s)


def algebraicky(s: Square) -> str:
    return chr(97 + s[1]) + str(8 - s[0])


class HerniPlocha:
    def __init__(self, starting: bool = True) -> None:
        self.pole: list[list[Figurka | None]] = [[None for _ in range(8)] for _ in range(8)]
        self.vyhozene_figurky_b: list[Figurka] = []
        self.vyhozene_figurky_c: list[Figurka] = []
        if starting:
            back = (Vez, Kun, Strelec, Dama, Kral, Strelec, Kun, Vez)
            for column, cls in enumerate(back):
                self.pole[0][column] = cls("black")
                self.pole[7][column] = cls("white")
                self.pole[1][column] = Pesak("black")
                self.pole[6][column] = Pesak("white")

    def kopie(self) -> HerniPlocha:
        other = HerniPlocha(False)
        other.pole = [row.copy() for row in self.pole]
        other.vyhozene_figurky_b = self.vyhozene_figurky_b.copy()
        other.vyhozene_figurky_c = self.vyhozene_figurky_c.copy()
        return other

    def vrat_obsah(self, s: Square) -> Figurka | None:
        return self.pole[s[0]][s[1]] if uvnitr(s) else None

    def poloz(self, s: Square, piece: Figurka | None) -> None:
        if not uvnitr(s):
            raise ValueError(f"Square outside board: {s!r}")
        self.pole[s[0]][s[1]] = piece

    def pole_figurek(self):
        for r in range(8):
            for c in range(8):
                piece = self.pole[r][c]
                if piece is not None:
                    yield (r,c),piece

    def kral(self, barva: str) -> Square | None:
        return next((s for s,p in self.pole_figurek() if p.barva == barva and isinstance(p, Kral)), None)

    def odstran(self, square: Square) -> Figurka | None:
        piece = self.vrat_obsah(square)
        self.poloz(square, None)
        if piece:
            (self.vyhozene_figurky_b if piece.barva == "white" else self.vyhozene_figurky_c).append(piece)
        return piece

    def presun(self, start: Square, end: Square) -> Figurka | None:
        piece = self.vrat_obsah(start)
        if piece is None:
            raise ValueError("No moving piece")
        taken = self.odstran(end)
        self.poloz(start, None)
        self.poloz(end, replace(piece, pohnuta=True))
        return taken

    def promenu(self, square: Square, code: str) -> None:
        pawn = self.vrat_obsah(square)
        if not isinstance(pawn, Pesak) or code not in PROMOTIONS:
            raise ValueError("Invalid promotion")
        self.poloz(square, PROMOTIONS[code](pawn.barva, True))

    def stav(self) -> tuple:
        """Immutable board fingerprint used by behavioral tests and the UI."""
        return tuple(tuple((type(p).__name__,p.barva,p.pohnuta) if p else None for p in row) for row in self.pole)
