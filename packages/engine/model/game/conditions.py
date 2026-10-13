"""Pure, bounded evaluation of game-supplied JSON conditions.

Only the game engine can register trusted query implementations. JSON never
contains import paths, callable names, source code or executable extensions.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any

from engine.model.game.schema import QUERIES, _bounded_json, condition, validate_reference

Query = Callable[[Mapping[str, Any]], Any]


class QueryResolutionError(ValueError):
    """A required trusted query cannot be evaluated safely."""


class ConditionEvaluator:
    """Evaluate validated JSON conditions against registered read-only queries."""

    def __init__(
        self, queries: Mapping[str, Query], references: Mapping[str, Any] | None = None
    ):
        """Register only recognized, trusted query primitives."""
        invalid = set(queries).difference(QUERIES)
        if invalid:
            raise QueryResolutionError(f"unknown query registrations: {sorted(invalid)}")
        self._queries = dict(queries)
        for name, value in (references or {}).items():
            validate_reference(name)
            _bounded_json(value)
        self._references = deepcopy(dict(references or {}))

    def resolve(self, value: Any) -> Any:
        """Resolve typed JSON reference nodes, never evaluating text as code."""
        if isinstance(value, dict):
            if set(value) == {"ref"}:
                name = value["ref"]
                validate_reference(name)
                if name not in self._references:
                    raise QueryResolutionError(f"unbound reference: {name}")
                return deepcopy(self._references[name])
            return {key: self.resolve(child) for key, child in value.items()}
        if isinstance(value, list):
            return [self.resolve(child) for child in value]
        return value

    def _query(self, name: str, params: Mapping[str, Any]) -> Any:
        """Resolve one whitelisted query or reject the unavailable operation."""
        primitive = self._queries.get(name)
        if primitive is None:
            raise QueryResolutionError(f"query is not implemented: {name}")
        value = primitive(self.resolve(dict(params)))
        _bounded_json(value)
        return value

    def _value(self, expression: Any) -> Any:
        """Resolve an immutable literal or a declared query reference."""
        if isinstance(expression, dict):
            if set(expression) == {"ref"}:
                return self.resolve(expression)
            return self._query(expression["query"], expression["params"])
        return expression

    def _compare(self, relation: str, left: Any, right: Any) -> bool:
        """Apply an explicitly selected comparison without coercion."""
        if relation == "eq":
            return type(left) is type(right) and left == right
        if relation == "ne":
            return type(left) is not type(right) or left != right
        if relation == "in":
            if isinstance(right, list):
                return left in right
            if isinstance(right, str) and isinstance(left, str):
                return left in right
            if isinstance(right, dict) and isinstance(left, (str, int, float, bool)):
                return left in right
            raise QueryResolutionError("membership requires compatible JSON types")
        if type(left) not in (int, float) or type(right) not in (int, float):
            raise QueryResolutionError("ordered comparison requires numeric operands")
        if relation == "lt":
            return left < right
        if relation == "lte":
            return left <= right
        if relation == "gt":
            return left > right
        if relation == "gte":
            return left >= right
        raise QueryResolutionError(f"unknown comparison relation: {relation}")

    def evaluate(self, expression: Mapping[str, Any]) -> bool:
        """Validate and interpret a bounded expression from a game JSON file."""
        condition(expression)

        def walk(node: Mapping[str, Any]) -> bool:
            op = node["op"]
            if op == "true":
                return True
            if op == "false":
                return False
            if op == "all":
                return all(walk(part) for part in node["args"])
            if op == "any":
                return any(walk(part) for part in node["args"])
            if op == "not":
                return not walk(node["arg"])
            if op == "test":
                result = self._query(node["query"], node["params"])
                if type(result) is not bool:
                    raise QueryResolutionError("predicate query must return a boolean")
                return result
            if op == "compare":
                return self._compare(
                    node["relation"],
                    self._value(node["left"]),
                    self._value(node["right"]),
                )
            raise QueryResolutionError(f"unsupported condition operation: {op}")

        return walk(expression)
