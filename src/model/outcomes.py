"""Pure game-neutral outcome arbitration from ordered declarative proposals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from model.conditions import QueryResolutionError
from model.hooks import PlannedEffect


@dataclass(frozen=True)
class Outcome:
    """Resolved game-owned result from a validated priority proposal."""

    kind: str
    cause: str
    winner: str | int | None
    priority: int


def resolve_outcome(effects: tuple[PlannedEffect, ...]) -> Outcome | None:
    """Choose highest declared priority, refusing contradictory top proposals."""
    candidates: list[Outcome] = []
    for effect in effects:
        if effect.op != "propose_outcome":
            continue
        props: dict[str, Any] = dict(effect.params)
        if set(props) != {"kind", "cause", "winner", "priority"}:
            raise QueryResolutionError("outcome proposals require four exact fields")
        winner = props["winner"]
        if winner is not None and type(winner) not in (str, int):
            raise QueryResolutionError("invalid outcome winner")
        if not isinstance(props["kind"], str) or not props["kind"]:
            raise QueryResolutionError("outcome kind must be a nonempty string")
        if not isinstance(props["cause"], str) or not props["cause"]:
            raise QueryResolutionError("outcome cause must be a nonempty string")
        priority = props["priority"]
        if type(priority) is not int or not -1000 <= priority <= 1000:
            raise QueryResolutionError("outcome priority must be a bounded integer")
        candidates.append(Outcome(props["kind"], props["cause"], winner, priority))
    if not candidates:
        return None
    highest = max(item.priority for item in candidates)
    top = [item for item in candidates if item.priority == highest]
    if any(item != top[0] for item in top[1:]):
        raise QueryResolutionError("conflicting outcomes have equal priority")
    return top[0]
