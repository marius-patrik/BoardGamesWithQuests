"""Immutable bounded capture-policy validation for declarative game definitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from model.conditions import QueryResolutionError

MAX_EVALUATION_WORK = 250000


class EvaluationBudgetExceeded(QueryResolutionError):
    """A trusted aggregate work ceiling was exhausted without accepting partial results."""


@dataclass
class EvaluationBudget:
    """Count shared deterministic work across one read, transition or replay.

    Args:
        limit: Trusted positive engine work ceiling, never supplied by game JSON.
        used: Consumed work units, initialized to zero.
        parent: Optional trusted aggregate counter charged with this child.
    """

    limit: int
    used: int = 0
    parent: EvaluationBudget | None = None

    def __post_init__(self) -> None:
        """Reject invalid trusted ceilings.

        Raises:
            ValueError: Limit or initial work count is invalid.
        """
        if (
            type(self.limit) is not int
            or self.limit < 1
            or type(self.used) is not int
            or self.used != 0
            or (self.parent is not None and not isinstance(self.parent, EvaluationBudget))
        ):
            raise ValueError("evaluation budget needs a positive integer ceiling")

    def consume(self, units: int = 1) -> None:
        """Atomically reserve deterministic work in this counter and every parent.

        Args:
            units: Nonnegative strict integer work cost.

        Raises:
            ValueError: Cost or the trusted parent hierarchy is invalid.
            EvaluationBudgetExceeded: Aggregate ceiling would be exceeded.
        """
        if type(units) is not int or units < 0:
            raise ValueError("evaluation cost must be a nonnegative integer")
        counters: list[EvaluationBudget] = []
        counter: EvaluationBudget | None = self
        while counter is not None:
            if not isinstance(counter, EvaluationBudget) or any(
                counter is entry for entry in counters
            ):
                raise ValueError("evaluation budget parent chain must be acyclic")
            if units > counter.limit - counter.used:
                raise EvaluationBudgetExceeded("aggregate evaluation work budget exceeded")
            counters.append(counter)
            counter = counter.parent
        # All reservations succeed before any counter changes, so rejection is atomic.
        for counter in counters:
            counter.used += units


@dataclass(frozen=True)
class CapturePolicy:
    """Declarative capture movement policy for a selected piece class."""

    flying: bool
    land_anywhere: bool
    deferred_removal: bool
    max_nodes: int = 4096

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> "CapturePolicy":
        """Require typed, explicitly declared capture semantics."""
        if set(obj) != {"flying", "land_anywhere", "deferred_removal", "max_nodes"}:
            raise QueryResolutionError("capture policy requires four explicit fields")
        if any(
            type(obj[key]) is not bool for key in ("flying", "land_anywhere", "deferred_removal")
        ):
            raise QueryResolutionError("capture booleans must be explicit")
        if obj["land_anywhere"] and not obj["flying"]:
            raise QueryResolutionError("extended landings require flying captures")
        n = obj["max_nodes"]
        if type(n) is not int or not 1 <= n <= 10000:
            raise QueryResolutionError("capture enumeration budget is invalid")
        return cls(obj["flying"], obj["land_anywhere"], obj["deferred_removal"], n)
