"""Board-neutral sequential capture enumeration driven entirely by piece vectors.

Supports single-square jumps and first-opponent ray captures with variable
landing distances. No branch refers to chess, draughts or a named piece.
This enumerator does not adjudicate mandatory capture, promotion or outcomes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from engine.model.game.board import Board
from engine.model.game.conditions import QueryResolutionError

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


class CaptureEnumerator:
    """Explore capture chains without modifying the original board."""

    def __init__(self, board: Board, budget: EvaluationBudget | None = None) -> None:
        """Bind geometry and the shared aggregate operation budget.

        Args:
            board: Position to inspect without mutation.
            budget: Shared trusted budget, or an independent bounded search budget.
        """
        self.board = board
        self.budget = budget if budget is not None else EvaluationBudget(MAX_EVALUATION_WORK)

    def enumerate(self, start: tuple[int, int], policy: CapturePolicy) -> list[dict[str, Any]]:
        """Produce bounded complete multi-hop capture paths from one square."""
        if not self.board.is_within_bounds(*start):
            raise QueryResolutionError("capture source is out of bounds")
        actor = self.board.get_piece_at(start)
        if actor is None:
            return []
        self.budget.consume(self.board.rows * self.board.cols)
        occupied = {
            (row, col): self.board.get_piece_at((row, col))
            for row in range(self.board.rows)
            for col in range(self.board.cols)
            if self.board.get_piece_at((row, col)) is not None
        }
        routes: list[dict[str, Any]] = []
        visited = 0

        def candidates(
            pos: tuple[int, int], placement: dict, already_captured: frozenset
        ) -> list[tuple]:
            found = []
            for dr, dc in actor.getAttackDirections():
                self.budget.consume()
                if (dr, dc) == (0, 0):
                    continue
                r, c = pos
                if policy.flying:
                    while True:
                        self.budget.consume()
                        r, c = r + dr, c + dc
                        if not self.board.is_within_bounds(r, c):
                            break
                        obstacle = placement.get((r, c))
                        if obstacle is None:
                            continue
                        if obstacle.getColor() == actor.getColor() or (r, c) in already_captured:
                            break
                        captured = (r, c)
                        nr, nc = r + dr, c + dc
                        while self.board.is_within_bounds(nr, nc) and (nr, nc) not in placement:
                            self.budget.consume()
                            found.append(((nr, nc), captured))
                            if not policy.land_anywhere:
                                break
                            nr, nc = nr + dr, nc + dc
                        break
                else:
                    enemy = (r + dr, c + dc)
                    landing = (r + 2 * dr, c + 2 * dc)
                    if not self.board.is_within_bounds(*landing):
                        continue
                    target = placement.get(enemy)
                    if (
                        target is not None
                        and target.getColor() != actor.getColor()
                        and enemy not in already_captured
                        and landing not in placement
                    ):
                        found.append((landing, enemy))
            return found

        def dfs(
            pos: tuple[int, int],
            placement: dict,
            steps: list[dict],
            already_captured: frozenset,
        ) -> None:
            nonlocal visited
            self.budget.consume()
            visited += 1
            if visited > policy.max_nodes:
                raise QueryResolutionError("capture search exceeded configured node budget")
            next_moves = candidates(pos, placement, already_captured)
            if not next_moves and steps:
                routes.append({"start": list(start), "steps": [dict(step) for step in steps]})
                if len(routes) > 128:
                    raise QueryResolutionError("too many capture routes")
            for landing, captured in next_moves:
                self.budget.consume(len(placement) + len(steps) + len(already_captured))
                if len(steps) >= 128:
                    raise QueryResolutionError("capture chain exceeds bounded depth")
                after = placement.copy()
                after.pop(pos)
                if not policy.deferred_removal:
                    after.pop(captured)
                after[landing] = actor
                step = {"landing": list(landing), "captured": list(captured)}
                dfs(landing, after, [*steps, step], already_captured | {captured})

        dfs(start, occupied, [], frozenset())
        return routes

    def for_side(self, side: int, policies: Mapping[str, CapturePolicy]) -> list[dict]:
        """Enumerate all capture routes using explicit per-kind policies."""
        if type(side) is not int or side not in (-1, 1):
            raise QueryResolutionError("invalid capture side")
        routes = []
        self.budget.consume(self.board.rows * self.board.cols)
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                piece = self.board.get_piece_at((row, col))
                if piece is None or piece.getColor() != side:
                    continue
                name = str(piece.getType())
                if name not in policies:
                    raise QueryResolutionError(f"missing capture policy for kind {name}")
                routes.extend(self.enumerate((row, col), policies[name]))
                if len(routes) > 128:
                    raise QueryResolutionError("too many capture routes")
        return routes
