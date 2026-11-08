"""One locally assigned player seat."""
from dataclasses import dataclass
from model.user import Uzivatel


@dataclass(frozen=True)
class Hrac:
    barva: str
    uzivatel: Uzivatel

    def __post_init__(self) -> None:
        if self.barva not in ("white", "black"):
            raise ValueError("Invalid player color")
