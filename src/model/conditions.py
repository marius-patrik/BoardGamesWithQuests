"""Pure, bounded evaluation of game-supplied JSON conditions.

Only the game engine can register trusted query implementations. JSON never
contains import paths, callable names, source code or executable extensions.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any

from model.schema import (
    MAX_JSON_TEXT_BYTES,
    QUERIES,
    _bounded_json,
    condition,
    validate_reference,
    thaw_json,
    _json_work,
)

Query = Callable[[Mapping[str, Any]], Any]


class QueryResolutionError(ValueError):
    """A required trusted query cannot be evaluated safely."""


class ConditionEvaluator:
    """Evaluate validated JSON conditions against registered read-only queries."""

    def __init__(
        self, queries: Mapping[str, Query], references: Mapping[str, Any] | None = None
    ) -> None:
        """Register only recognized, trusted query primitives."""
        invalid = set(queries).difference(QUERIES)
        if invalid:
            raise QueryResolutionError(f"unknown query registrations: {sorted(invalid)}")
        self._queries = dict(queries)
        self._work: Callable[[int], None] = lambda units: None
        for name, value in (references or {}).items():
            validate_reference(name)
            if name == "event.claim" and isinstance(value, str):
                if (
                    len(value) > MAX_JSON_TEXT_BYTES
                    or len(value.encode("utf-8")) > MAX_JSON_TEXT_BYTES
                ):
                    raise ValueError("claim reference exceeds the configuration byte bound")
            else:
                _bounded_json(value)
        self._references = deepcopy(dict(references or {}))

    def resolve(self, value: Any) -> Any:
        """Resolve bounded references and nested whitelisted query-value nodes.

        Args:
            value: Schema-validated literal or typed data expression.

        Returns:
            Detached JSON data with references and queries resolved.

        Raises:
            QueryResolutionError: A reference or required query is unavailable or invalid.
        """
        self._work(1 + (len(value) // 64 if isinstance(value, str) else 0))
        if isinstance(value, Mapping):
            if set(value) == {"ref"}:
                name = value["ref"]
                validate_reference(name)
                if name not in self._references:
                    raise QueryResolutionError(f"unbound reference: {name}")
                return deepcopy(self._references[name])
            if set(value) == {"query", "params"}:
                return deepcopy(self._query(value["query"], value["params"]))
            return {key: self.resolve(child) for key, child in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.resolve(child) for child in value]
        return value

    def _query(self, name: str, params: Mapping[str, Any]) -> Any:
        """Resolve one whitelisted query or reject the unavailable operation."""
        primitive = self._queries.get(name)
        if primitive is None:
            raise QueryResolutionError(f"query is not implemented: {name}")
        value = primitive(self.resolve(dict(params)))
        _bounded_json(value)
        self._work(3 * _json_work(value))
        return value

    def _value(self, expression: Any) -> Any:
        """Resolve an immutable literal or a declared query reference."""
        if isinstance(expression, Mapping):
            if set(expression) == {"ref"}:
                return self.resolve(expression)
            return self._query(expression["query"], expression["params"])
        return self.resolve(expression)

    def _equal(self, left: Any, right: Any) -> bool:
        """Compare JSON values recursively without boolean or numeric coercion.

        Args:
            left: First validated JSON value.
            right: Second validated JSON value.

        Returns:
            Whether every corresponding value has the same type and value.
        """
        self._work(
            1
            + (
                max(len(left), len(right)) // 64
                if isinstance(left, str) and isinstance(right, str)
                else 0
            )
        )
        if type(left) is not type(right):
            return False
        if isinstance(left, list):
            return len(left) == len(right) and all(self._equal(a, b) for a, b in zip(left, right))
        if isinstance(left, dict):
            self._work(len(left))
            return left.keys() == right.keys() and all(
                self._equal(value, right[key]) for key, value in left.items()
            )
        return left == right

    def _compare(self, relation: str, left: Any, right: Any) -> bool:
        """Apply an explicitly selected comparison without JSON type coercion.

        Args:
            relation: Validated equality, membership or numeric comparison.
            left: Resolved left JSON operand.
            right: Resolved right JSON operand.

        Returns:
            Whether the requested typed relation holds.

        Raises:
            QueryResolutionError: Operands are incompatible with the relation.
        """
        if relation == "eq":
            return self._equal(left, right)
        if relation == "ne":
            return not self._equal(left, right)
        if relation == "in":
            if isinstance(right, list):
                return any(self._equal(left, item) for item in right)
            if isinstance(right, str) and isinstance(left, str):
                return left in right
            if isinstance(right, dict) and isinstance(left, str):
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
        return self._evaluate_validated(expression)

    def _evaluate_validated(self, expression: Mapping[str, Any]) -> bool:
        """Interpret a program-owned expression validated before freezing.

        Args:
            expression: Immutable node from a validated rule program.

        Returns:
            The condition result without repeating static schema traversal.
        """

        def walk(node: Mapping[str, Any]) -> bool:
            self._work(1)
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
