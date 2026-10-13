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


@dataclass(frozen=True)
class CapturePolicy:
    """Declarative capture movement policy for a selected piece class."""

    flying: bool
    land_anywhere: bool
    max_nodes: int = 4096

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> "CapturePolicy":
        """Require typed, explicitly declared capture semantics."""
        if set(obj) != {"flying", "land_anywhere", "max_nodes"}:
            raise QueryResolutionError("capture policy requires three explicit fields")
        if type(obj["flying"]) is not bool or type(obj["land_anywhere"]) is not bool:
            raise QueryResolutionError("capture booleans must be explicit")
        if obj["land_anywhere"] and not obj["flying"]:
            raise QueryResolutionError("extended landings require flying captures")
        n = obj["max_nodes"]
        if type(n) is not int or not 1 <= n <= 10000:
            raise QueryResolutionError("capture enumeration budget is invalid")
        return cls(obj["flying"], obj["land_anywhere"], n)


class CaptureEnumerator:
    """Explore capture chains without modifying the original board."""

    def __init__(self, board: Board):
        """Read positions and side-specific vectors from the supplied board."""
        self.board = board

    def enumerate(self, start: tuple[int, int], policy: CapturePolicy) -> list[dict[str, Any]]:
        """Produce bounded complete multi-hop capture paths from one square."""
        if not self.board.is_within_bounds(*start):
            raise QueryResolutionError("capture source is out of bounds")
        actor = self.board.get_piece_at(start)
        if actor is None:
            return []
        occupied = {
            (row, col): self.board.get_piece_at((row, col))
            for row in range(self.board.rows)
            for col in range(self.board.cols)
            if self.board.get_piece_at((row, col)) is not None
        }
        routes: list[dict[str, Any]] = []
        visited = 0

        def candidates(pos: tuple[int, int], placement: dict) -> list[tuple]:
            found = []
            for dr, dc in actor.getAttackDirections():
                if (dr, dc) == (0, 0):
                    continue
                r, c = pos
                if policy.flying:
                    while True:
                        r, c = r + dr, c + dc
                        if not self.board.is_within_bounds(r, c):
                            break
                        obstacle = placement.get((r, c))
                        if obstacle is None:
                            continue
                        if obstacle.getColor() == actor.getColor():
                            break
                        captured = (r, c)
                        nr, nc = r + dr, c + dc
                        while self.board.is_within_bounds(nr, nc) and (nr, nc) not in placement:
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
                        and landing not in placement
                    ):
                        found.append((landing, enemy))
            return found

        def dfs(pos: tuple[int, int], placement: dict, steps: list[dict]) -> None:
            nonlocal visited
            visited += 1
            if visited > policy.max_nodes:
                raise QueryResolutionError("capture search exceeded configured node budget")
            next_moves = candidates(pos, placement)
            if not next_moves and steps:
                routes.append({"start": list(start), "steps": [dict(step) for step in steps]})
                if len(routes) > 128:
                    raise QueryResolutionError("too many capture routes")
            for landing, captured in next_moves:
                after = placement.copy()
                after.pop(pos)
                after.pop(captured)
                after[landing] = actor
                step = {"landing": list(landing), "captured": list(captured)}
                dfs(landing, after, [*steps, step])

        dfs(start, occupied, [])
        return routes

    def for_side(self, side: int, policies: Mapping[str, CapturePolicy]) -> list[dict]:
        """Enumerate all capture routes using explicit per-kind policies."""
        if type(side) is not int or side not in (-1, 1):
            raise QueryResolutionError("invalid capture side")
        routes = []
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
