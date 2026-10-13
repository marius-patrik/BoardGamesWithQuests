"""Per-participant quest progress, separate from immutable quest definitions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from engine.model.game.quest import Quest


@dataclass(frozen=True)
class QuestCompletion:
    """Completion of one quest for one participant in one game."""

    game_id: str
    player_id: str
    quest_name: str
    reward_points: int


class QuestManager:
    """Registry of declarative definitions and independently scoped completions."""

    def __init__(self, quests: Iterable[Quest] = ()):
        """Initialize a catalog without sharing player completion state."""
        self.quests: dict[str, Quest] = {}
        self.completed: dict[tuple[str, str], set[str]] = {}
        for quest in quests:
            self.register_quest(quest)

    def register_quest(self, quest: Quest) -> None:
        """Add an immutable definition, rejecting conflicting names."""
        if quest.name in self.quests:
            raise ValueError(f"duplicate quest definition: {quest.name}")
        self.quests[quest.name] = quest

    def get_quests(self) -> list[Quest]:
        """Return immutable catalog definitions."""
        return list(self.quests.values())

    def complete(self, game_id: str, player_id: str, quest_name: str) -> QuestCompletion:
        """Record one validated completion at most once for a specific participant.

        This method records *only* an already authorized completion. Eligibility
        must first be established by configured hooks in the authoritative game.
        """
        if not all(isinstance(x, str) and x for x in (game_id, player_id, quest_name)):
            raise ValueError("game, participant and quest identifiers are required")
        if quest_name not in self.quests:
            raise ValueError(f"unknown quest: {quest_name}")
        key = (game_id, player_id)
        seen = self.completed.setdefault(key, set())
        if quest_name in seen:
            raise ValueError("quest already completed for this participant")
        seen.add(quest_name)
        return QuestCompletion(
            game_id, player_id, quest_name, self.quests[quest_name].reward_points
        )

    def get_completed_quests(self, game_id: str, player_id: str) -> list[Quest]:
        """Get completions for exactly one game and participant."""
        return [
            self.quests[name] for name in sorted(self.completed.get((game_id, player_id), set()))
        ]

    def check_quests(self, context: Any, user: Any = None) -> list[Quest]:
        """Reject unconfigured quest evaluation instead of sharing completion."""
        raise NotImplementedError("quests must be evaluated by JSON-configured hooks")
