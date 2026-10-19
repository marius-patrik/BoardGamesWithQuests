"""Immutable bounded capture-policy validation for declarative game definitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from model.game.conditions import QueryResolutionError


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

