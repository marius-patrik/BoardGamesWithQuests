"""Immutable chess pieces. Movement vectors are implemented by the rule engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Figurka:
    barva: str
    pohnuta: bool = False
    kod: ClassVar[str] = "?"
    nazev: ClassVar[str] = "Piece"
    vektory: ClassVar[tuple[tuple[int, int], ...]] = ()
    vektory_utoku: ClassVar[tuple[tuple[int, int], ...]] = ()

    def __post_init__(self) -> None:
        if self.barva not in ("white", "black"):
            raise ValueError("Invalid piece color")


class Kral(Figurka):
    kod = "K"
    nazev = "King"
    vektory = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    vektory_utoku = vektory


class Dama(Figurka):
    kod = "Q"
    nazev = "Queen"
    vektory = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    vektory_utoku = vektory


class Vez(Figurka):
    kod = "R"
    nazev = "Rook"
    vektory = ((-1, 0), (0, -1), (0, 1), (1, 0))
    vektory_utoku = vektory


class Strelec(Figurka):
    kod = "B"
    nazev = "Bishop"
    vektory = ((-1, -1), (-1, 1), (1, -1), (1, 1))
    vektory_utoku = vektory


class Kun(Figurka):
    kod = "N"
    nazev = "Knight"
    vektory = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
    vektory_utoku = vektory


class Pesak(Figurka):
    kod = "P"
    nazev = "Pawn"


PROMOTIONS = {"Q": Dama, "R": Vez, "B": Strelec, "N": Kun}
PIECES = {cls.kod: cls for cls in (Kral, Dama, Vez, Strelec, Kun, Pesak)}
SYMBOLS = {
    "white": dict(zip("KQRBNP", "♔♕♖♗♘♙")),
    "black": dict(zip("KQRBNP", "♚♛♜♝♞♟")),
}
