"""Versioned, bounded declarative condition/trigger validation.

This module only validates configuration. It does not imply that a game can yet
execute the validated operation set; no arbitrary string is ever evaluated as code.
"""

from __future__ import annotations

from typing import Any
import math

MAX_DEPTH = 12
MAX_NODES = 256
MAX_RULES = 128
MAX_QUESTS = 128
HOOKS = frozenset({"permits_move", "available_moves", "outcome", "on_move_made", "status"})
QUERIES = frozenset(
    {
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
    }
)
RELATIONS = frozenset({"eq", "ne", "lt", "lte", "gt", "gte", "in"})

REF_ROOTS = frozenset({"move", "player", "clock", "board", "game", "quest", "event", "rule"})


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
    """Validate reference nodes inside query or effect parameters."""
    if isinstance(value, dict):
        if "ref" in value:
            if set(value) != {"ref"}:
                raise ValueError("a reference node may contain only ref")
            validate_reference(value["ref"])
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
    """Validate finite rule/quest definitions with no executable extensions."""
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
            _check_params(effect["params"])
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
