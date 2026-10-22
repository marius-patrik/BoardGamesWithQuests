"""Immutable complete move intent, with no executable piece/board behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, init=False)
class Move:
    """One exact JSON candidate: a source, complete landing path and promotion."""

    start_pos: tuple[int, int]
    hops: tuple[tuple[int, int], ...]
    promotion: str | None

    @staticmethod
    def _square(value: Any) -> tuple[int, int]:
        if (
            not isinstance(value, (list, tuple))
            or len(value) != 2
            or any(type(axis) is not int or not 0 <= axis <= 255 for axis in value)
        ):
            raise ValueError("move square must be a bounded integer pair")
        return (value[0], value[1])

    def __init__(
        self,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        *,
        hops: tuple[tuple[int, int], ...] | None = None,
        promotion: str | None = None,
    ) -> None:
        start = self._square(start_pos)
        end = self._square(end_pos)
        landings = (end,) if hops is None else tuple(self._square(hop) for hop in hops)
        if not 1 <= len(landings) <= 128 or landings[-1] != end:
            raise ValueError("complete capture path must end at the destination")
        if start == landings[0]:
            raise ValueError("source and first landing cannot match")
        if promotion is not None and (
            type(promotion) is not str or not 1 <= len(promotion) <= 128
        ):
            raise ValueError("promotion must name a bounded configured kind")
        object.__setattr__(self, "start_pos", start)
        object.__setattr__(self, "hops", landings)
        object.__setattr__(self, "promotion", promotion)

    @property
    def end_pos(self) -> tuple[int, int]:
        return self.hops[-1]

    @classmethod
    def from_json(cls, data: Any) -> Move:
        """Reject extra keys, executable values and malformed intents."""
        if not isinstance(data, dict) or set(data) != {"start", "hops", "promotion"}:
            raise ValueError("move intent must contain exactly start/hops/promotion")
        if not isinstance(data["start"], list):
            raise ValueError("JSON start must be an array")
        if not isinstance(data["hops"], list) or not 1 <= len(data["hops"]) <= 128:
            raise ValueError("JSON hops must be a bounded nonempty array")
        if any(not isinstance(hop, list) for hop in data["hops"]):
            raise ValueError("JSON landing squares must be arrays")
        landing = data["hops"][-1]
        return cls(
            cls._square(data["start"]),
            cls._square(landing),
            hops=tuple(cls._square(hop) for hop in data["hops"]),
            promotion=data["promotion"],
        )

    def to_json(self) -> dict[str, Any]:
        """Return only inert JSON; never leak Python piece objects."""
        return {
            "start": list(self.start_pos),
            "hops": [list(square) for square in self.hops],
            "promotion": self.promotion,
        }
