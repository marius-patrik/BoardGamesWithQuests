"""Pure evaluation of declared hooks into a deterministic, non-applying effect plan."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from engine.model.game.conditions import ConditionEvaluator, Query
from engine.model.game.schema import HOOKS, validate_hooks


@dataclass(frozen=True)
class PlannedEffect:
    """Trusted generic effect name and data; never a callable or board mutation."""

    op: str
    params: Mapping[str, Any]


@dataclass(frozen=True)
class HookEvaluation:
    """Ordered matched rule identifiers and effects for an authoritative executor."""

    matched_rule_ids: tuple[str, ...]
    effects: tuple[PlannedEffect, ...]


class HookInterpreter:
    """Compile and evaluate bounded game JSON without applying effects."""

    def __init__(self, rules: list[dict[str, Any]], queries: Mapping[str, Query]):
        """Validate rules and copy their JSON data out of the mutable editor."""
        validate_hooks(rules, [])
        self._rules = tuple(deepcopy(rules))
        self._conditions = ConditionEvaluator(queries)

    def evaluate(self, hook: str) -> HookEvaluation:
        """Collect matching effects in declared order, without authorizing them."""
        if hook not in HOOKS:
            raise ValueError(f"unknown game hook: {hook!r}")
        matched: list[str] = []
        effects: list[PlannedEffect] = []
        for rule in self._rules:
            if rule["hook"] != hook:
                continue
            if self._conditions.evaluate(rule["when"]):
                matched.append(rule["id"])
                effects.extend(
                    PlannedEffect(effect["op"], deepcopy(effect["params"]))
                    for effect in rule["effects"]
                )
        return HookEvaluation(tuple(matched), tuple(effects))
