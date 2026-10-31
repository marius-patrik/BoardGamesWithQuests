"""Versioned declarative validation, immutable data and traversal accounting.

The declarative schema only validates configuration. It does not imply that a game can yet
execute the validated operation set; no arbitrary string is ever evaluated as code.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping
from types import MappingProxyType
import math


def _json_work(value: Any) -> int:
    """Measure deterministic JSON traversal and text-copy work.

    Args:
        value: Bounded validated JSON or its immutable representation.

    Returns:
        Nodes plus one work unit per 64 text characters.
    """
    if isinstance(value, Mapping):
        return 1 + sum(1 + _json_work(child) for child in value.values())
    if isinstance(value, (list, tuple)):
        return 1 + sum(_json_work(child) for child in value)
    return 1 + (len(value) // 64 if isinstance(value, str) else 0)


MAX_DEPTH = 12
MAX_NODES = 256
MAX_JSON_TEXT_BYTES = 262144
MAX_RULES = 128
MAX_QUESTS = 128
HOOKS = frozenset({"permits_move", "available_moves", "outcome", "on_move_made"})
QUERIES = frozenset(
    {
        "integer",
        "json_value",
        "square_offset",
        "pieces_safe",
        "piece_at",
        "pieces_matching",
        "path_clear",
        "squares_attacked",
        "capture_paths",
        "capture_count",
        "legal_move_count",
        "repetition_count",
        "halfmove_count",
        "clock_remaining",
        "rule_state",
        "move_attribute",
        "board_dimension",
        "participant",
        "turn",
        "history_count",
        "last_action",
        "position",
        "promotion_options",
        "special_rights",
        "temporary_target",
        "quest_progress",
    }
)
EFFECTS = frozenset(
    {
        "permit",
        "deny",
        "offer_move",
        "move_piece",
        "capture_piece",
        "replace_piece",
        "set_state",
        "increment_state",
        "record_event",
        "propose_outcome",
        "complete_quest",
        "set_clock",
        "set_rights",
        "set_target",
    }
)
RELATIONS = frozenset({"eq", "ne", "lt", "lte", "gt", "gte", "in"})

REF_ROOTS = frozenset({"move", "player", "clock", "board", "game", "quest", "event", "rule"})


def freeze_json(value: Any, depth: int = 0, budget: list[int] | None = None) -> Any:
    """Copy JSON into recursively immutable mappings and tuples.

    Args:
        value: JSON-compatible value to detach from its source.
        depth: Internal recursion depth.
        budget: Shared internal document node budget.

    Returns:
        Immutable JSON value, with objects as read-only mappings and arrays as tuples.

    Raises:
        ValueError: Data is not finite JSON or exceeds document bounds.
    """
    if budget is None:
        budget = [65536]
    budget[0] -= 1
    if depth > 32 or budget[0] < 0:
        raise ValueError("JSON document exceeds complexity limits")
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is int and value.bit_length() <= 64:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, Mapping) and all(type(key) is str for key in value):
        return MappingProxyType(
            {key: freeze_json(child, depth + 1, budget) for key, child in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(child, depth + 1, budget) for child in value)
    raise ValueError("document must contain finite bounded JSON data")


def thaw_json(value: Any) -> Any:
    """Copy immutable JSON into independently writable serialization values.

    Args:
        value: Value produced by :func:`freeze_json`, or ordinary JSON data.

    Returns:
        Detached dictionaries, lists and JSON scalar values.
    """
    if isinstance(value, Mapping):
        return {key: thaw_json(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw_json(child) for child in value]
    return value


def validate_effect(op: str, params: Any, allow_references: bool = True) -> None:
    """Validate the exact data contract of one trusted effect operation.

    Args:
        op: Whitelisted generic operation name.
        params: Operation parameters as a JSON object.
        allow_references: Whether unresolved typed references may appear as values.

    Raises:
        ValueError: Operation, parameter keys, types or literal bounds are invalid.
    """
    _check_params(params)
    contracts = {
        "permit": (set(), {"reason", "target"}),
        "deny": (set(), {"reason", "target"}),
        "offer_move": ({"start", "end"}, {"hops", "promotion", "effects"}),
        "move_piece": ({"start", "end"}, set()),
        "capture_piece": ({"square"}, set()),
        "replace_piece": ({"square", "kind"}, set()),
        "set_state": ({"name", "value"}, set()),
        "increment_state": ({"name", "amount"}, set()),
        "record_event": ({"name"}, {"payload"}),
        "propose_outcome": ({"kind", "cause", "winner", "priority"}, set()),
        "complete_quest": ({"quest", "player"}, set()),
        "set_clock": ({"player", "seconds"}, set()),
        "set_rights": ({"name", "value"}, set()),
        "set_target": ({"name", "value"}, set()),
    }
    if op not in contracts:
        raise ValueError("unknown effect operation")
    required, optional = contracts[op]
    if not required <= set(params) or not set(params) <= required | optional:
        raise ValueError(f"{op} has missing or unknown parameters")

    def expression(value: Any) -> bool:
        """Recognize bounded typed expressions without treating text as code."""
        if isinstance(value, dict):
            return set(value) in ({"ref"}, {"query", "params"}) or any(
                expression(child) for child in value.values()
            )
        return isinstance(value, list) and any(expression(child) for child in value)

    for name, value in params.items():
        if allow_references and expression(value):
            continue
        if isinstance(value, dict) and set(value) == {"ref"}:
            if not allow_references:
                raise ValueError("resolved effects cannot contain references")
            validate_reference(value["ref"])
            continue
        if name in {"start", "end", "square", "target"}:
            if (
                not isinstance(value, list)
                or len(value) != 2
                or any(type(axis) is not int or not 0 <= axis <= 255 for axis in value)
            ):
                raise ValueError(f"{op}.{name} needs a bounded JSON square")
        elif name in {"reason", "name", "kind", "cause", "quest"}:
            if not isinstance(value, str) or not value or len(value) > 128:
                raise ValueError(f"{op}.{name} must be a nonempty bounded string")
        elif name in {"player", "winner"}:
            if value is None and name == "winner":
                continue
            if not (
                (type(value) is int and value in (-1, 1))
                or (isinstance(value, str) and value and len(value) <= 128)
            ):
                raise ValueError(f"{op}.{name} needs a participant identity")
        elif name == "priority":
            if type(value) is not int or not -1000 <= value <= 1000:
                raise ValueError("outcome priority must be a bounded integer")
        elif name == "amount":
            if type(value) is not int or not -(2**63) < value < 2**63:
                raise ValueError("state increment must be a bounded integer")
        elif name == "seconds":
            if type(value) is not int or not 0 <= value <= 315360000:
                raise ValueError("clock seconds must be a nonnegative bounded integer")
        elif name == "value" and op == "set_rights" and type(value) is not bool:
            raise ValueError("special right must be boolean")
        elif name == "value" and op == "set_target":
            if value is not None and (
                not isinstance(value, list)
                or len(value) != 2
                or any(type(axis) is not int or not 0 <= axis <= 255 for axis in value)
            ):
                raise ValueError("temporary target must be a bounded square or null")
        elif name == "promotion":
            if value is not None and (not isinstance(value, str) or not value or len(value) > 128):
                raise ValueError("offered promotion must name a configured kind")
        elif name == "hops":
            if not isinstance(value, list) or not 1 <= len(value) <= 128:
                raise ValueError("offered hops must be a bounded nonempty array")
            for square in value:
                if (
                    not isinstance(square, list)
                    or len(square) != 2
                    or any(type(axis) is not int or not 0 <= axis <= 255 for axis in square)
                ):
                    raise ValueError("offered landing must be a bounded square")
            if value[-1] != params["end"]:
                raise ValueError("offered final landing must match end")
        elif name == "effects":
            if not isinstance(value, list) or len(value) > 32:
                raise ValueError("offered effects must be a bounded array")
            for effect in value:
                if (
                    not isinstance(effect, dict)
                    or set(effect) != {"op", "params"}
                    or not isinstance(effect["op"], str)
                    or effect["op"]
                    not in {
                        "move_piece",
                        "capture_piece",
                        "replace_piece",
                        "set_state",
                        "increment_state",
                        "set_rights",
                        "set_target",
                        "record_event",
                    }
                ):
                    raise ValueError("offer contains an unsupported transition effect")
                validate_effect(effect["op"], effect["params"], allow_references)
        elif name == "payload" and not isinstance(value, dict):
            raise ValueError("event payload must be a JSON object")
    if not allow_references:

        def reject_reference(value: Any) -> None:
            if isinstance(value, dict):
                if "ref" in value or "query" in value:
                    raise ValueError("resolved effects cannot contain expressions")
                for child in value.values():
                    reject_reference(child)
            elif isinstance(value, list):
                for child in value:
                    reject_reference(child)

        reject_reference(params)


def validate_reference(value: Any) -> None:
    """Allow bounded typed references into the trusted hook context only."""
    if not isinstance(value, str) or len(value) > 96:
        raise ValueError("reference must be a short string")
    path = value.split(".")
    if not 2 <= len(path) <= 4 or path[0] not in REF_ROOTS:
        raise ValueError("unrecognized reference root or path depth")
    if any(not part.isidentifier() or part.startswith("_") for part in path):
        raise ValueError("reference contains an invalid identifier")


def validate_embedded_references(value: Any) -> None:
    """Validate bounded reference and nested query nodes in data parameters.

    Args:
        value: Bounded JSON literal or typed expression tree.

    Raises:
        ValueError: A reference, nested query name or expression shape is invalid.
    """
    if isinstance(value, dict):
        if "ref" in value:
            if set(value) != {"ref"}:
                raise ValueError("a reference node may contain only ref")
            validate_reference(value["ref"])
        elif "query" in value:
            if (
                set(value) != {"query", "params"}
                or not isinstance(value["query"], str)
                or value["query"] not in QUERIES
            ):
                raise ValueError("unknown or malformed nested query")
            _check_params(value["params"])
        else:
            for child in value.values():
                validate_embedded_references(child)
    elif isinstance(value, list):
        for child in value:
            validate_embedded_references(child)


def _bounded_json(value: Any, depth: int = 0, budget: list[int] | None = None) -> None:
    """Enforce typed finite JSON without executable or unbounded structures."""
    if budget is None:
        budget = [MAX_NODES]
    budget[0] -= 1
    if budget[0] < 0 or depth > MAX_DEPTH:
        raise ValueError("configuration expression exceeds complexity limits")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value.bit_length() > 64:
            raise ValueError("integer exceeds bounded range")
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite JSON number")
        return
    if isinstance(value, str):
        if len(value) > 1024:
            raise ValueError("configuration string exceeds 1024 characters")
        return
    if isinstance(value, list):
        if len(value) > 128:
            raise ValueError("configuration array too long")
        for child in value:
            _bounded_json(child, depth + 1, budget)
        return
    if isinstance(value, dict):
        if len(value) > 64 or any(not isinstance(k, str) or len(k) > 100 for k in value):
            raise ValueError("invalid configuration object keys")
        for child in value.values():
            _bounded_json(child, depth + 1, budget)
        return
    raise ValueError("configuration must contain JSON-compatible data")


def _check_params(value: Any) -> None:
    """Check bounded, literal parameters without interpreting identifiers as code."""
    if not isinstance(value, dict):
        raise ValueError("query/effect params must be an object")
    _bounded_json(value)
    validate_embedded_references(value)


def _value(value: Any, depth: int) -> None:
    """Validate a scalar literal or a whitelisted query value."""
    if isinstance(value, dict):
        if set(value) == {"ref"}:
            validate_reference(value["ref"])
            return
        if (
            set(value) != {"query", "params"}
            or not isinstance(value["query"], str)
            or value["query"] not in QUERIES
        ):
            raise ValueError("value expression needs a recognized query and params")
        _check_params(value["params"])
        return
    if value is None or type(value) in (bool, int, float, str, list):
        _bounded_json(value, depth)
        return
    raise ValueError("value must be literal or a typed query")


def condition(expr: Any, depth: int = 0, budget: list[int] | None = None) -> None:
    """Check the small typed condition AST recursively."""
    if budget is None:
        budget = [MAX_NODES]
    budget[0] -= 1
    if budget[0] < 0 or depth > MAX_DEPTH:
        raise ValueError("condition expression exceeds complexity limits")
    if not isinstance(expr, dict):
        raise ValueError("condition must be a tagged object")
    op = expr.get("op")
    if not isinstance(op, str):
        raise ValueError("condition operation must be a string")
    if op in ("true", "false"):
        if set(expr) != {"op"}:
            raise ValueError("literal condition has unexpected keys")
    elif op in ("all", "any"):
        if set(expr) != {"op", "args"} or not isinstance(expr["args"], list) or not expr["args"]:
            raise ValueError("logical condition needs nonempty args")
        for child in expr["args"]:
            condition(child, depth + 1, budget)
    elif op == "not":
        if set(expr) != {"op", "arg"}:
            raise ValueError("not condition needs one argument")
        condition(expr["arg"], depth + 1, budget)
    elif op == "test":
        if (
            set(expr) != {"op", "query", "params"}
            or not isinstance(expr["query"], str)
            or expr["query"] not in QUERIES
        ):
            raise ValueError("test condition needs a recognized query")
        _check_params(expr["params"])
    elif op == "compare":
        if (
            set(expr) != {"op", "relation", "left", "right"}
            or not isinstance(expr["relation"], str)
            or expr["relation"] not in RELATIONS
        ):
            raise ValueError("comparison has unknown relation or fields")
        _value(expr["left"], depth + 1)
        _value(expr["right"], depth + 1)
    else:
        raise ValueError(f"unknown condition operation: {op!r}")


def validate_hooks(rules: Any, quests: Any) -> None:
    """Validate finite rule/quest definitions and operation-specific effects.

    Args:
        rules: Untrusted decoded JSON hook definitions.
        quests: Untrusted decoded JSON quest definitions.

    Raises:
        ValueError: Fields, references, types or expression bounds are invalid.
    """
    if not isinstance(rules, list) or len(rules) > MAX_RULES:
        raise ValueError("rules must be a bounded list")
    if not isinstance(quests, list) or len(quests) > MAX_QUESTS:
        raise ValueError("quests must be a bounded list")
    ids: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"id", "hook", "when", "effects"}:
            raise ValueError("rule fields must be id/hook/when/effects")
        if not isinstance(rule["hook"], str) or rule["hook"] not in HOOKS:
            raise ValueError("unknown rule hook")
        if not isinstance(rule["id"], str) or not rule["id"] or rule["id"] in ids:
            raise ValueError("duplicate or invalid rule id")
        ids.add(rule["id"])
        condition(rule["when"])
        effects = rule["effects"]
        if not isinstance(effects, list) or len(effects) > 32:
            raise ValueError("rule effects must be a bounded list")
        for effect in effects:
            if (
                not isinstance(effect, dict)
                or set(effect) != {"op", "params"}
                or not isinstance(effect["op"], str)
                or effect["op"] not in EFFECTS
            ):
                raise ValueError("unknown effect or malformed effect fields")
            validate_effect(effect["op"], effect["params"])
    quest_ids: set[str] = set()
    for quest in quests:
        if not isinstance(quest, dict) or set(quest) != {"id", "description", "when", "reward"}:
            raise ValueError("quest fields must be id/description/when/reward")
        qid = quest["id"]
        if not isinstance(qid, str) or not qid or qid in quest_ids:
            raise ValueError("duplicate or invalid quest id")
        quest_ids.add(qid)
        if not isinstance(quest["description"], str):
            raise ValueError("quest description must be text")
        if type(quest["reward"]) is not int or quest["reward"] < 0:
            raise ValueError("quest reward must be non-negative integer")
        condition(quest["when"])
