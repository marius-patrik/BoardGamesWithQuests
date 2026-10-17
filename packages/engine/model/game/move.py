"""Immutable, game-neutral ordered-hop move intents.

An intent contains no piece objects, capture assertions or executable behavior.
The authoritative game manager derives captures and applies validated transitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

Square = tuple[int, int]


@dataclass(frozen=True)
class Move:
    """A source, ordered landing sequence and optional configured promotion.

    Args:
        start_pos: Nonnegative source coordinates.
        end_pos: Final landing coordinates.
        hops: Complete ordered landing sequence; empty means one hop.
        promotion: Configuration-owned replacement kind, or None.

    Raises:
        ValueError: Coordinates, sequence or promotion are malformed.
    """

    start_pos: Square
    end_pos: Square
    hops: tuple[Square, ...] = ()
    promotion: str | None = None

    def __post_init__(self) -> None:
        """Copy coordinates and reject ambiguous or malformed intents.

        Raises:
            ValueError: A coordinate, sequence or promotion is invalid.
        """
        if not isinstance(self.hops, (tuple, list)) or len(self.hops) > 128:
            raise ValueError("move hops must be a bounded sequence")
        for square in (self.start_pos, self.end_pos, *self.hops):
            if (
                not isinstance(square, (tuple, list))
                or len(square) != 2
                or any(type(axis) is not int or axis < 0 for axis in square)
            ):
                raise ValueError("move coordinates must be nonnegative integer pairs")
        start, end = tuple(self.start_pos), tuple(self.end_pos)
        hops = tuple(tuple(square) for square in self.hops) or (end,)
        if hops[-1] != end or any(a == b for a, b in zip((start, *hops), hops)):
            raise ValueError("move landings must end at destination without empty hops")
        if self.promotion is not None and (
            not isinstance(self.promotion, str) or not 1 <= len(self.promotion) <= 128
        ):
            raise ValueError("promotion must name a configured piece kind")
        object.__setattr__(self, "start_pos", start)
        object.__setattr__(self, "end_pos", end)
        object.__setattr__(self, "hops", hops)

    def to_json(self) -> dict[str, Any]:
        """Return detached JSON data with every landing preserved.

        Returns:
            Exact move intent fields suitable for transport and persistence.
        """
        return {
            "start": list(self.start_pos),
            "hops": [list(square) for square in self.hops],
            "promotion": self.promotion,
        }

    @classmethod
    def from_json(cls, value: Mapping[str, Any]) -> Move:
        """Parse the closed transport contract without trusting capture claims.

        Args:
            value: JSON object containing start, hops and promotion.

        Returns:
            An immutable validated intent.

        Raises:
            ValueError: Fields, JSON coordinate types or sequence are invalid.
        """
        if not isinstance(value, dict) or set(value) != {"start", "hops", "promotion"}:
            raise ValueError("move requires exactly start, hops and promotion")
        hops = value["hops"]
        if (
            not isinstance(value["start"], list)
            or not isinstance(hops, list)
            or not hops
            or any(not isinstance(square, list) for square in hops)
        ):
            raise ValueError("move coordinates must be JSON arrays")
        return cls(value["start"], hops[-1], hops, value["promotion"])

    def execute(self, board: Any) -> bool:
        """Reject mutation outside the authoritative transition boundary.

        Args:
            board: Any attempted mutation target.

        Raises:
            PermissionError: Intents cannot mutate a board directly.
        """
        raise PermissionError("moves must be committed through GameManager")
