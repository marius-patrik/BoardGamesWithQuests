"""Finite, read-only generic history and rule-state queries for JSON hooks.

All values come from a previously validated authoritative snapshot. Unknown
state is an error, never a guessed right, target or outcome.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from engine.model.game.conditions import QueryResolutionError
from engine.model.game.schema import _bounded_json


class SnapshotQueries:
    """Expose typed metadata primitives without branches on a game's identity."""

    def __init__(self, snapshot: Mapping[str, Any]):
        """Validate the complete bounded snapshot before exposing queries."""
        _bounded_json(dict(snapshot))
        self._snapshot = dict(snapshot)

    @staticmethod
    def _key(params: Mapping[str, Any], allowed: set[str], required: set[str]) -> None:
        """Refuse ambiguous or unknown query parameters."""
        if (
            not isinstance(params, Mapping)
            or not required <= set(params)
            or not set(params) <= allowed
        ):
            raise QueryResolutionError("unrecognized or missing snapshot query parameters")

    def _field(self, field: str) -> Any:
        """Reject unavailable instead of inventing a game-significant default."""
        if field not in self._snapshot:
            raise QueryResolutionError(f"snapshot field is unavailable: {field}")
        return self._snapshot[field]

    def _lookup(self, field: str, params: Mapping[str, Any]) -> Any:
        self._key(params, {"name"}, {"name"})
        name = params["name"]
        if not isinstance(name, str) or not name:
            raise QueryResolutionError("snapshot key must be a nonempty string")
        values = self._field(field)
        if not isinstance(values, dict) or name not in values:
            raise QueryResolutionError(f"unknown {field} identifier: {name}")
        return values[name]

    def rule_state(self, params: Mapping[str, Any]) -> Any:
        """Look up bounded game-owned state, including capture-chain counters."""
        return self._lookup("rule_state", params)

    def special_rights(self, params: Mapping[str, Any]) -> Any:
        """Return explicitly recorded rights, such as castling eligibility."""
        return self._lookup("special_rights", params)

    def temporary_target(self, params: Mapping[str, Any]) -> Any:
        """Return transient targets, such as an eligible en-passant square."""
        return self._lookup("temporary_targets", params)

    def move_attribute(self, params: Mapping[str, Any]) -> Any:
        """Return generic candidate metadata, including a capture count."""
        return self._lookup("move_attributes", params)

    def promotion_options(self, params: Mapping[str, Any]) -> Any:
        """Return promotion choices from a configured and validated snapshot."""
        self._key(params, {"side"}, {"side"})
        side = params["side"]
        if side not in ("active", "opponent"):
            raise QueryResolutionError("promotion side must be active or opponent")
        data = self._field("promotion_options")
        if not isinstance(data, dict) or not isinstance(data.get(side), list):
            raise QueryResolutionError("promotion options are unavailable")
        return data[side]

    def repetition_count(self, params: Mapping[str, Any]) -> int:
        """Count exact canonical position keys in committed history."""
        self._key(params, {"scope"}, {"scope"})
        if params["scope"] != "position":
            raise QueryResolutionError("only the exact current position scope is supported")
        key = self._field("position_key")
        positions = self._field("position_history")
        if not isinstance(key, str) or not isinstance(positions, list):
            raise QueryResolutionError("invalid position history")
        if any(not isinstance(item, str) for item in positions):
            raise QueryResolutionError("position history must contain canonical strings")
        return sum(position == key for position in positions)

    def clock_remaining(self, params: Mapping[str, Any]) -> int:
        self._key(params, {"side"}, {"side"})
        side = params["side"]
        clocks = self._field("clocks")
        if side not in ("active", "opponent") or not isinstance(clocks, dict):
            raise QueryResolutionError("invalid clock selector")
        value = clocks.get(side)
        if type(value) is not int or value < 0:
            raise QueryResolutionError("clock value missing or invalid")
        return value

    def capture_count(self, params: Mapping[str, Any]) -> int:
        """Count captures in a candidate or calculate the declared maximum."""
        self._key(params, {"scope"}, {"scope"})
        scope = params["scope"]
        if scope == "candidate":
            value = self.move_attribute({"name": "captures"})
        elif scope == "maximum":
            paths = self._field("capture_paths")
            if not isinstance(paths, list):
                raise QueryResolutionError("capture paths are not computed")
            if any(
                not isinstance(path, dict) or not isinstance(path.get("steps"), list)
                for path in paths
            ):
                raise QueryResolutionError("malformed capture route")
            value = max((len(path["steps"]) for path in paths), default=0)
        else:
            raise QueryResolutionError("unknown capture scope")
        if type(value) is not int or value < 0:
            raise QueryResolutionError("invalid capture count")
        return value

    def capture_paths(self, params: Mapping[str, Any]) -> bool:
        """Report availability of precomputed capture paths; never synthesize them."""
        self._key(params, {"side"}, {"side"})
        if params["side"] not in ("active", "opponent"):
            raise QueryResolutionError("invalid capture side")
        paths = self._field("capture_paths")
        if not isinstance(paths, list):
            raise QueryResolutionError("missing complete capture path enumeration")
        return bool(paths)

    def history_count(self, params: Mapping[str, Any]) -> int:
        self._key(params, set(), set())
        history = self._field("events")
        if not isinstance(history, list):
            raise QueryResolutionError("history must be an array")
        return len(history)

    def bindings(self) -> dict[str, Callable[[Mapping[str, Any]], Any]]:
        """Expose only the context queries with implementations."""
        return {
            "rule_state": self.rule_state,
            "special_rights": self.special_rights,
            "temporary_target": self.temporary_target,
            "move_attribute": self.move_attribute,
            "promotion_options": self.promotion_options,
            "repetition_count": self.repetition_count,
            "clock_remaining": self.clock_remaining,
            "capture_count": self.capture_count,
            "capture_paths": self.capture_paths,
            "history_count": self.history_count,
        }
