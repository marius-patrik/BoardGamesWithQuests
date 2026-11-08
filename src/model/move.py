"""Immutable chess move identity and coordinate-free resignation action."""
from __future__ import annotations
from dataclasses import dataclass
from model.board import Square, uvnitr


@dataclass(frozen=True)
class Tah:
    odkud: Square
    kam: Square
    typ_tahu: str = "normal"
    promena: str | None = None

    def __post_init__(self) -> None:
        if not uvnitr(self.odkud) or not uvnitr(self.kam) or self.odkud == self.kam:
            raise ValueError("Invalid move coordinates")
        if self.promena is not None and self.promena not in {"Q", "R", "B", "N"}:
            raise ValueError("Invalid promotion piece")


@dataclass(frozen=True)
class Akce:
    typ: str
    tah: Tah | None = None

    @classmethod
    def move(cls, tah: Tah) -> Akce:
        return cls("move", tah)

    @classmethod
    def resign(cls) -> Akce:
        return cls("resign")
