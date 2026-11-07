"""Pure evaluation of declared hooks into a deterministic, non-applying effect plan."""

from __future__ import annotations

from collections.abc import Mapping, Callable
from dataclasses import dataclass
from typing import Any

from model.conditions import ConditionEvaluator, Query, QueryResolutionError
from model.schema import HOOKS, freeze_json, thaw_json, validate_effect, validate_hooks


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


class RuleProgram:
    """Own validated immutable rules indexed by lifecycle hook.

    This representation carries only static game data. Query implementations and
    references are bound separately for each evaluation and never retained.
    """

    def __init__(self, rules: Any) -> None:
        """Validate and freeze detached rules once.

        Args:
            rules: Bounded declarative rule sequence.

        Raises:
            ValueError: The rule sequence violates the closed schema.
        """
        detached = thaw_json(rules)
        validate_hooks(detached, [])
        frozen = freeze_json(detached)
        self._hooks = {
            hook: tuple(rule for rule in frozen if rule["hook"] == hook) for hook in HOOKS
        }

    def rules(self, hook: str) -> tuple[Mapping[str, Any], ...]:
        """Return immutable rules for one recognized hook.

        Args:
            hook: Recognized lifecycle name.

        Returns:
            Program-owned immutable rule nodes in declared order.

        Raises:
            ValueError: The hook is unknown.
        """
        if hook not in self._hooks:
            raise ValueError(f"unknown game hook: {hook!r}")
        return self._hooks[hook]

    def evaluate(
        self,
        hook: str,
        queries: Mapping[str, Query],
        references: Mapping[str, Any] | None = None,
        work: Callable[[int], None] | None = None,
    ) -> HookEvaluation:
        """Evaluate immutable rules with operation-local facts.

        Args:
            hook: Recognized lifecycle name.
            queries: Trusted query bindings for the explicit position.
            references: Explicit immutable-context values.
            work: Aggregate reservation callback for actual visited rule nodes.

        Returns:
            Ordered matches and resolved immutable effect plans.

        Raises:
            ValueError: Hook or query bindings are invalid.
            QueryResolutionError: A required fact or work reservation fails.
        """
        evaluator = ConditionEvaluator(queries, references)
        if work is not None:
            evaluator._work = work
        matched = []
        effects = []
        for rule in self.rules(hook):
            evaluator._work(1)
            if evaluator._evaluate_validated(rule["when"]):
                matched.append(rule["id"])
                effects.extend(
                    PlannedEffect(effect["op"], evaluator.resolve(effect["params"]))
                    for effect in rule["effects"]
                )
        return HookEvaluation(tuple(matched), tuple(effects))


class HookInterpreter:
    """Compile and evaluate bounded game JSON without applying effects."""

    def __init__(
        self,
        rules: list[dict[str, Any]],
        queries: Mapping[str, Query],
        references: Mapping[str, Any] | None = None,
    ) -> None:
        """Validate rules and detach their JSON data from the mutable editor.

        Args:
            rules: Declarative hook definitions, including frozen snapshots.
            queries: Trusted query implementations keyed by whitelisted operation.
            references: Bound immutable-context reference values.

        Raises:
            ValueError: Rules, query names or references are invalid.
        """
        self._program = RuleProgram(rules)
        self._conditions = ConditionEvaluator(queries, references)

    def evaluate(self, hook: str, work: Callable[[int], None] | None = None) -> HookEvaluation:
        """Collect validated immutable effects without authorizing or applying them.

        Args:
            hook: One recognized lifecycle hook.
            work: Optional trusted aggregate reservation callback.

        Returns:
            Ordered matched rule identities and immutable resolved effects.

        Raises:
            ValueError: Hook, query resolution or resolved effect data is invalid.
        """
        return self._program.evaluate(
            hook, self._conditions._queries, self._conditions._references, work=work
        )
