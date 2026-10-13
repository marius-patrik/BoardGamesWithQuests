"""Immutable declarative quest metadata; evaluation belongs to the rules interpreter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Quest:
    """A game-supplied JSON quest definition, not shared completion state.

    Args:
        name: Identifier of the quest within its configuration.
        description: Text shown to participants.
        condition: Validated expression AST, evaluated by the generic engine.
        reward_points: Non-negative experience reward.
    """

    name: str
    description: str
    condition: Mapping[str, Any]
    reward_points: int

    def __post_init__(self) -> None:
        """Reject invalid definitions before progress instances exist."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("quest name must be nonempty")
        if not isinstance(self.condition, Mapping):
            raise TypeError("quest condition must be declarative JSON")
        if type(self.reward_points) is not int or self.reward_points < 0:
            raise ValueError("quest reward must be a non-negative integer")

    def validate(self, context: Any = None) -> bool:
        """Fail closed until the versioned condition interpreter is connected."""
        raise NotImplementedError("quest evaluation requires validated JSON hooks")
