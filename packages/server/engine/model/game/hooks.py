"""Pure evaluation of declared hooks into a deterministic, non-applying effect plan."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from server.engine.model.game.conditions import ConditionEvaluator, Query
from server.engine.model.game.schema import (
    HOOKS,
    freeze_json,
    thaw_json,
    validate_effect,
    validate_hooks,
)


@dataclass(frozen=True)
class PlannedEffect:
    """Trusted generic effect name and data; never a callable or board mutation."""

    op: str
    params: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Detach and freeze validated resolved effect parameters.

        Raises:
            ValueError: Resolved parameters violate their operation contract.
        """
        detached = thaw_json(self.params)
        validate_effect(self.op, detached, allow_references=False)
        object.__setattr__(self, "params", freeze_json(detached))


@dataclass(frozen=True)
class HookEvaluation:
    """Ordered matched rule identifiers and effects for an authoritative executor."""

    matched_rule_ids: tuple[str, ...]
    effects: tuple[PlannedEffect, ...]


class HookInterpreter:
    """Compile and evaluate bounded game JSON without applying effects."""

    def __init__(
        self,
        rules: list[dict[str, Any]],
        queries: Mapping[str, Query],
        references: Mapping[str, Any] | None = None,
    ):
        """Validate rules and detach their JSON data from the mutable editor.

        Args:
            rules: Declarative hook definitions, including frozen snapshots.
            queries: Trusted query implementations keyed by whitelisted operation.
            references: Bound immutable-context reference values.

        Raises:
            ValueError: Rules, query names or references are invalid.
        """
        rules = thaw_json(rules)
        validate_hooks(rules, [])
        self._rules = tuple(deepcopy(rules))
        self._conditions = ConditionEvaluator(queries, references)

    def evaluate(self, hook: str) -> HookEvaluation:
        """Collect validated immutable effects without authorizing or applying them.

        Args:
            hook: One recognized lifecycle hook.

        Returns:
            Ordered matched rule identities and immutable resolved effects.

        Raises:
            ValueError: Hook, query resolution or resolved effect data is invalid.
        """
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
                    PlannedEffect(effect["op"], self._conditions.resolve(effect["params"]))
                    for effect in rule["effects"]
                )
        return HookEvaluation(tuple(matched), tuple(effects))
