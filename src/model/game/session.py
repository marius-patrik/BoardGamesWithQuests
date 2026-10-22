"""Permanent local desktop-session boundary over authoritative JSON game transitions.

The desktop UI sends intent, actor and revision; it never owns mutable engine
state. The same domain manager can later be hosted without this local adapter.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
import time
import uuid

from model.game.definition import load_bundled_definition
from model.game.manager import GameManager, TransitionError


class DesktopSession:
    """An independently owned, local two-player game lifecycle."""

    def __init__(self, game: str = "chess") -> None:
        self._clock_floor_ms = 0
        self._generation = 0
        self._game_name = game
        self._manager = self._new_manager(game)

    def _now(self) -> int:
        # Wall-clock milliseconds survive process restarts. Never regress
        # below the persisted accepted event's timestamp.
        now = max(time.time_ns() // 1_000_000, self._clock_floor_ms)
        self._clock_floor_ms = now
        return now

    def _new_manager(self, game: str) -> GameManager:
        definition = load_bundled_definition(game)
        started = self._now()
        return GameManager(
            definition,
            game_id=uuid.uuid4().hex,
            participant_ids=("white", "black"),
            started_at_ms=started,
        )

    @property
    def game(self) -> str:
        return self._game_name

    def snapshot(self) -> dict[str, Any]:
        """Return a detached, self-contained authoritative state and event history."""
        return self._manager.get_state()

    def legal_actions(self) -> list[dict[str, Any]]:
        """Return complete player-selectable moves, never live piece objects."""
        return [move.to_json() for move in self._manager.get_valid_moves()]

    def submit(
        self,
        actor: str,
        expected_revision: int,
        action: dict[str, Any],
        *,
        action_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply one authorized intent and return its event plus updated snapshot.

        An explicit action ID enables safe retries after uncertain UI delivery.
        """
        ident = action_id if action_id is not None else uuid.uuid4().hex
        event = self._manager.submit_action(actor, expected_revision, ident, action, self._now())
        return {"event": event, "state": self.snapshot()}

    def reset(self, game: str | None = None) -> dict[str, Any]:
        """Start a new isolated session, optionally switching installed games."""
        selected = self._game_name if game is None else game
        manager = self._new_manager(selected)
        self._manager = manager
        self._game_name = selected
        self._generation += 1
        return self.snapshot()

    @classmethod
    def recover(cls, snapshot: Mapping[str, Any]) -> "DesktopSession":
        """Verify saved state by deterministic replay before exposing it."""
        manager = GameManager.from_snapshot(snapshot)
        result = object.__new__(cls)
        result._manager = manager
        result._game_name = {"chess": "chess", "english_draughts": "checkers"}.get(
            manager.definition.name, manager.definition.name
        )
        result._clock_floor_ms = manager.get_state()["clocks"]["anchor_ms"]
        result._generation = 0
        return result
