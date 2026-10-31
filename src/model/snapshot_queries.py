"""Read-only typed history and rule-state queries over authoritative JSON.

Side-indexed fields use explicit ``active`` and ``opponent`` keys, relative to
one bound turn. Missing facts never imply permission, completion or a default.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any

from model.conditions import QueryResolutionError


class SnapshotQueries:
    """Bind an isolated finite JSON snapshot to game-neutral query operations."""

    def __init__(self, snapshot: Mapping[str, Any]) -> None:
        """Copy a bounded snapshot without accepting non-JSON container coercion.

        Args:
            snapshot: Authoritative field mapping with JSON-only nested values.

        Raises:
            QueryResolutionError: Values are non-JSON, nonfinite or oversized.
        """
        if not isinstance(snapshot, Mapping):
            raise QueryResolutionError("snapshot must be a JSON object")
        try:
            self._json_value(dict(snapshot), 0)
            serialized = json.dumps(dict(snapshot), allow_nan=False)
        except (TypeError, ValueError, OverflowError, RecursionError) as error:
            raise QueryResolutionError("snapshot must be finite JSON") from error
        if len(serialized.encode("utf-8")) > 1048576:
            raise QueryResolutionError("snapshot query context exceeds 1 MiB")
        self._snapshot = json.loads(serialized)

    @staticmethod
    def _json_value(value: Any, depth: int) -> None:
        """Reject coercible Python objects and excessive nesting.

        Args:
            value: Candidate JSON value.
            depth: Container depth from the snapshot root.

        Raises:
            QueryResolutionError: Value exceeds the finite JSON contract.
        """
        if depth > 64:
            raise QueryResolutionError("snapshot nesting exceeds 64 levels")
        if type(value) in (str, int, bool) or value is None:
            return
        if type(value) is float and math.isfinite(value):
            return
        if type(value) is list:
            for child in value:
                SnapshotQueries._json_value(child, depth + 1)
            return
        if type(value) is dict and all(type(key) is str for key in value):
            for child in value.values():
                SnapshotQueries._json_value(child, depth + 1)
            return
        raise QueryResolutionError("snapshot must contain only finite JSON values")

    @staticmethod
    def _key(params: Mapping[str, Any], allowed: set[str], required: set[str]) -> None:
        """Validate query keys.

        Args:
            params: Supplied query parameters.
            allowed: Accepted keys.
            required: Mandatory keys.

        Raises:
            QueryResolutionError: Keys are unknown or missing.
        """
        if not isinstance(params, Mapping) or not required <= set(params) <= allowed:
            raise QueryResolutionError("unrecognized or missing snapshot query parameters")

    def _field(self, field: str) -> Any:
        """Read an isolated field.

        Args:
            field: Authoritative snapshot key.

        Returns:
            A defensive copy of the stored JSON value.

        Raises:
            QueryResolutionError: The field is unavailable.
        """
        if field not in self._snapshot:
            raise QueryResolutionError(f"snapshot field is unavailable: {field}")
        return deepcopy(self._snapshot[field])

    def _lookup(self, field: str, params: Mapping[str, Any]) -> Any:
        """Look up a named value.

        Args:
            field: Snapshot map key.
            params: Exactly one nonempty ``name`` string.

        Returns:
            An isolated named JSON value.

        Raises:
            QueryResolutionError: Parameters or identifier are invalid.
        """
        self._key(params, {"name"}, {"name"})
        name = params["name"]
        if not isinstance(name, str) or not name:
            raise QueryResolutionError("snapshot key must be a nonempty string")
        values = self._field(field)
        if not isinstance(values, dict) or name not in values:
            raise QueryResolutionError(f"unknown {field} identifier: {name}")
        return values[name]

    def _side_value(self, field: str, params: Mapping[str, Any]) -> Any:
        """Read an explicitly selected side value.

        Args:
            field: Side-indexed snapshot field.
            params: Exactly ``side`` with ``active`` or ``opponent``.

        Returns:
            A defensive copy of the requested value.

        Raises:
            QueryResolutionError: Side or selected value is unavailable.
        """
        self._key(params, {"side"}, {"side"})
        side = params["side"]
        if not isinstance(side, str) or side not in ("active", "opponent"):
            raise QueryResolutionError("side must be active or opponent")
        values = self._field(field)
        if not isinstance(values, dict) or side not in values:
            raise QueryResolutionError(f"side value is unavailable: {field}")
        return values[side]

    @staticmethod
    def _count(value: Any) -> int:
        """Validate a count.

        Args:
            value: Candidate integer count.

        Returns:
            The nonnegative strict integer.

        Raises:
            QueryResolutionError: Value is negative or not an integer.
        """
        if type(value) is not int or value < 0:
            raise QueryResolutionError("count must be a nonnegative integer")
        return value

    def rule_state(self, params: Mapping[str, Any]) -> Any:
        """Read named mutable rule state.

        Args:
            params: Exactly a nonempty ``name``.

        Returns:
            Copied JSON state.

        Raises:
            QueryResolutionError: Name or state is unavailable.
        """
        return self._lookup("rule_state", params)

    def special_rights(self, params: Mapping[str, Any]) -> Any:
        """Read an explicitly recorded right.

        Args:
            params: Exactly a nonempty ``name``.

        Returns:
            Copied JSON rights value.

        Raises:
            QueryResolutionError: Name or rights are unavailable.
        """
        return self._lookup("special_rights", params)

    def temporary_target(self, params: Mapping[str, Any]) -> Any:
        """Read an explicitly recorded temporary target.

        Args:
            params: Exactly a nonempty ``name``.

        Returns:
            Copied target value, including an explicit null.

        Raises:
            QueryResolutionError: Name or target is unavailable.
        """
        return self._lookup("temporary_targets", params)

    def move_attribute(self, params: Mapping[str, Any]) -> Any:
        """Read candidate metadata.

        Args:
            params: Exactly a nonempty ``name``.

        Returns:
            Copied JSON candidate attribute.

        Raises:
            QueryResolutionError: Name or candidate attribute is unavailable.
        """
        return self._lookup("move_attributes", params)

    def promotion_options(self, params: Mapping[str, Any]) -> list[str]:
        """Read explicit configured promotion kinds for one side.

        Args:
            params: Exactly ``side`` selecting active or opponent.

        Returns:
            Isolated list of nonempty piece-kind strings.

        Raises:
            QueryResolutionError: Options are missing or malformed.
        """
        value = self._side_value("promotion_options", params)
        if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
            raise QueryResolutionError("promotion options must be piece-kind strings")
        return value

    def repetition_count(self, params: Mapping[str, Any]) -> int:
        """Count exact canonical position keys in committed history.

        Args:
            params: Exactly ``scope`` set to ``position``.

        Returns:
            Number of occurrences of ``position_key`` in ``position_history``.

        Raises:
            QueryResolutionError: Scope or bounded string history is invalid.
        """
        self._key(params, {"scope"}, {"scope"})
        if params["scope"] != "position":
            raise QueryResolutionError("only the exact current position scope is supported")
        key = self._field("position_key")
        positions = self._field("position_history")
        if not isinstance(key, str) or not isinstance(positions, list) or len(positions) > 4096:
            raise QueryResolutionError("invalid position history")
        if any(not isinstance(item, str) for item in positions):
            raise QueryResolutionError("position history must contain canonical strings")
        return sum(position == key for position in positions)

    def clock_remaining(self, params: Mapping[str, Any]) -> int:
        """Read authoritative remaining clock units for a side.

        Args:
            params: Exactly ``side`` selecting active or opponent.

        Returns:
            Nonnegative integer from ``clocks[side]``.

        Raises:
            QueryResolutionError: Clock is unavailable or invalid.
        """
        return self._count(self._side_value("clocks", params))

    @staticmethod
    def _square(value: Any) -> tuple[int, int]:
        """Validate explicit nonnegative coordinates without inferring board size.

        Args:
            value: JSON row/column pair.

        Returns:
            Immutable strict-integer coordinate pair.

        Raises:
            QueryResolutionError: Coordinate shape or values are invalid.
        """
        if not isinstance(value, list) or len(value) != 2:
            raise QueryResolutionError("capture coordinate must be a row/column pair")
        if any(type(x) is not int or x < 0 for x in value):
            raise QueryResolutionError("capture coordinates must be nonnegative integers")
        return value[0], value[1]

    def _capture_routes(self, side: str) -> list[dict[str, Any]]:
        """Validate complete precomputed routes without deriving legality.

        Args:
            side: Explicit active/opponent selector.

        Returns:
            Copied routes with canonical start and ordered capture steps.

        Raises:
            QueryResolutionError: Side maps or bounded route structures are invalid.
        """
        paths = self._field("capture_paths")
        if not isinstance(paths, dict) or set(paths) != {"active", "opponent"}:
            raise QueryResolutionError("capture paths require explicit active and opponent maps")
        for routes in paths.values():
            if not isinstance(routes, list) or len(routes) > 128:
                raise QueryResolutionError("capture routes must be bounded arrays")
            for route in routes:
                if not isinstance(route, dict) or set(route) != {"start", "steps"}:
                    raise QueryResolutionError("malformed capture route")
                current = self._square(route["start"])
                steps = route["steps"]
                if not isinstance(steps, list) or not 1 <= len(steps) <= 128:
                    raise QueryResolutionError("capture steps must be nonempty and bounded")
                captured_squares: set[tuple[int, int]] = set()
                for step in steps:
                    if not isinstance(step, dict) or set(step) != {"landing", "captured"}:
                        raise QueryResolutionError("malformed capture step")
                    landing = self._square(step["landing"])
                    captured = self._square(step["captured"])
                    if captured in captured_squares or captured in (current, landing):
                        raise QueryResolutionError("invalid or duplicate captured square")
                    captured_squares.add(captured)
                    current = landing
        return paths[side]

    def capture_count(self, params: Mapping[str, Any]) -> int:
        """Read candidate captures or the active participant's maximum.

        Args:
            params: Exactly ``scope`` set to ``candidate`` or ``maximum``.

        Returns:
            Candidate count or maximum active route length, zero for no routes.

        Raises:
            QueryResolutionError: Count, selector or routes are invalid.
        """
        self._key(params, {"scope"}, {"scope"})
        if params["scope"] == "candidate":
            return self._count(self.move_attribute({"name": "captures"}))
        if params["scope"] == "maximum":
            return max((len(path["steps"]) for path in self._capture_routes("active")), default=0)
        raise QueryResolutionError("unknown capture scope")

    def capture_paths(self, params: Mapping[str, Any]) -> bool:
        """Report capture availability exclusively for the selected side.

        Args:
            params: Exactly ``side`` selecting active or opponent.

        Returns:
            Whether the selected complete route enumeration is nonempty.

        Raises:
            QueryResolutionError: Side or enumeration is invalid.
        """
        self._key(params, {"side"}, {"side"})
        side = params["side"]
        if not isinstance(side, str) or side not in ("active", "opponent"):
            raise QueryResolutionError("invalid capture side")
        return bool(self._capture_routes(side))

    def history_count(self, params: Mapping[str, Any]) -> int:
        """Count committed event objects.

        Args:
            params: Empty parameter object.

        Returns:
            Length of the bounded ``events`` list.

        Raises:
            QueryResolutionError: Parameters or event history are invalid.
        """
        self._key(params, set(), set())
        history = self._field("events")
        if (
            not isinstance(history, list)
            or len(history) > 4096
            or any(not isinstance(event, dict) for event in history)
        ):
            raise QueryResolutionError("history must be a bounded array of event objects")
        return len(history)

    def halfmove_count(self, params: Mapping[str, Any]) -> int:
        """Read an explicitly tracked reversible-action count.

        Args:
            params: Empty parameter object.

        Returns:
            Nonnegative ``halfmove_count`` integer.

        Raises:
            QueryResolutionError: Parameters or stored count are invalid.
        """
        self._key(params, set(), set())
        return self._count(self._field("halfmove_count"))

    def last_action(self, params: Mapping[str, Any]) -> dict[str, Any] | None:
        """Read the recorded last action, including explicit absence.

        Args:
            params: Empty parameter object.

        Returns:
            Copied ``last_action`` object or explicit null before any action.

        Raises:
            QueryResolutionError: Parameters or stored action are invalid.
        """
        self._key(params, set(), set())
        value = self._field("last_action")
        if value is not None and not isinstance(value, dict):
            raise QueryResolutionError("last action must be an object or explicit null")
        return value

    def legal_move_count(self, params: Mapping[str, Any]) -> int:
        """Read a precomputed authoritative legal-action count.

        Args:
            params: Exactly ``side`` selecting active or opponent.

        Returns:
            Nonnegative integer from ``legal_move_counts[side]``.

        Raises:
            QueryResolutionError: No validated legal-action count is available.
        """
        return self._count(self._side_value("legal_move_counts", params))

    def participant(self, params: Mapping[str, Any]) -> dict[str, Any]:
        """Read a bound participant's verified identity metadata.

        Args:
            params: Exactly ``side`` selecting active or opponent.

        Returns:
            Copied ``participants[side]`` object with nonempty id and side +/-1.

        Raises:
            QueryResolutionError: Participant identity metadata is malformed.
        """
        value = self._side_value("participants", params)
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("id"), str)
            or not value["id"]
            or type(value.get("side")) is not int
            or value["side"] not in (-1, 1)
        ):
            raise QueryResolutionError("participant requires a nonempty id and explicit side")
        return value

    def position(self, params: Mapping[str, Any]) -> dict[str, Any]:
        """Read the supplied canonical position data without deriving fields.

        Args:
            params: Empty parameter object.

        Returns:
            Copied ``position`` JSON object supplied by the authoritative session.

        Raises:
            QueryResolutionError: Parameters or position are invalid.
        """
        self._key(params, set(), set())
        value = self._field("position")
        if not isinstance(value, dict):
            raise QueryResolutionError("position must be an explicit object")
        return value

    def quest_progress(self, params: Mapping[str, Any]) -> dict[str, Any]:
        """Read participant-scoped progress for one configured quest.

        Args:
            params: Exactly ``side`` (active/opponent) and nonempty quest ``name``.

        Returns:
            Copied progress with nonnegative active, positive target and completed boolean.

        Raises:
            QueryResolutionError: Quest, side or progress values are invalid.
        """
        self._key(params, {"side", "name"}, {"side", "name"})
        quests = self._side_value("quest_progress", {"side": params["side"]})
        name = params["name"]
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(quests, dict)
            or name not in quests
        ):
            raise QueryResolutionError("quest progress identifier is unavailable")
        value = quests[name]
        if not isinstance(value, dict) or set(value) != {"active", "target", "completed"}:
            raise QueryResolutionError("quest progress requires active, target and completed")
        self._count(value["active"])
        if (
            type(value["target"]) is not int
            or value["target"] <= 0
            or type(value["completed"]) is not bool
        ):
            raise QueryResolutionError("quest target or completion is invalid")
        return value

    def bindings(self) -> dict[str, Callable[[Mapping[str, Any]], Any]]:
        """Expose the implemented immutable snapshot query vocabulary.

        Returns:
            Trusted query names mapped to bound pure operations.
        """
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
            "halfmove_count": self.halfmove_count,
            "last_action": self.last_action,
            "legal_move_count": self.legal_move_count,
            "participant": self.participant,
            "position": self.position,
            "quest_progress": self.quest_progress,
        }
