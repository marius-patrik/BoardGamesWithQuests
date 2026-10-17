#!/usr/bin/env python3
"""Validate implementation-owned portable JSON and relational file declarations.

Static conformance only: no claims about deployed migrations, real identity,
transactional gameplay, private RLS, revision conflicts or verified user paths.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
GAME_KEYS = ("chess", "english-draughts", "international-draughts", "moneyproperty")


def walk(value):
    """Traverse nested JSON and OpenAPI AST values, including array members."""
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def validate_data() -> dict[str, object]:
    """Check every built-in definition and its references against portable schema and operators."""
    schema = json.loads((DATA / "configuration.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    operator_registry = json.loads((DATA / "operators.json").read_text())["operators"]
    hooks = set(
        re.findall(
            r"\('([a-z_]+(?:\.[a-z_]+)+)',\s*\d+",
            (ROOT / "packages/server/supabase/migrations/seed.sql").read_text(),
        )
    )
    counts = {"games": 0, "seeds": 0, "actions": 0, "operators": set()}
    for name in GAME_KEYS:
        doc = json.loads((DATA / f"{name}.json").read_text())
        jsonschema.validate(doc, schema)
        assert doc["definition"]["key"] == name, f"{name}: key mismatch"
        keyed = {}
        for group in ("entities", "seeds", "roles", "phases"):
            rows = doc[group]
            keys = [r["key"] for r in rows]
            assert len(keys) == len(set(keys)), f"{name}: duplicate {group} key"
            keyed[group] = {r["key"]: r for r in rows}
        entities, seeds, roles, phases = (
            keyed[k] for k in ("entities", "seeds", "roles", "phases")
        )
        assert sum(e["kind"] == "game" for e in entities.values()) == 1, f"{name}: root entity type"
        assert (
            sum(entities.get(s["type"], {}).get("kind") == "game" for s in seeds.values()) == 1
        ), f"{name}: root seed"
        assert sum(bool(p["initial"]) for p in phases.values()) == 1, f"{name}: initial phase"
        lo, hi = doc["definition"]["min_participants"], doc["definition"]["max_participants"]
        assert 1 <= lo <= hi <= 64, f"{name}: participant cardinality"
        assert (
            sum(r["min"] for r in roles.values())
            <= lo
            <= hi
            <= sum(r["max"] for r in roles.values())
        ), f"{name}: role allocation"
        field_map = {(f["entity"], f["key"]): f for f in doc["fields"]}
        assert len(field_map) == len(doc["fields"]), f"{name}: duplicate fields"
        for s in seeds.values():
            assert s["type"] in entities, f'{name}: missing entity type {s["type"]}'
            for k in ("parent", "location"):
                if k in s:
                    assert s[k] in seeds, f'{name}: seed {s["key"]} unresolved {k}'
            if "location" in s:
                assert (
                    entities[seeds[s["location"]]["type"]]["kind"] == "space"
                ), f"{name}: invalid space location"
            for key, val in s.get("values", {}).items():
                assert (
                    s["type"],
                    key,
                ) in field_map, f'{name}: seed {s["key"]} undefined field {key}'
            if "owner" in s:
                assert 0 <= s["owner"] < hi, f"{name}: invalid owner seat"
        for link in doc["links"]:
            assert (
                link["source"] in seeds and link["target"] in seeds
            ), f"{name}: dangling topology link"
        for attr in ("parent", "location"):
            for seed_key in seeds:
                curr = seed_key
                seen = {curr}
                while attr in seeds[curr]:
                    curr = seeds[curr][attr]
                    assert curr not in seen, f"{name}: seed cycle {seed_key}.{attr}"
                    seen.add(curr)
        for visual in doc["visuals"]:
            assert visual["entity"] in entities, f"{name}: dangling visual binding"
        action_keys = set()
        for action in doc["actions"]:
            aid = f'{name}:{action["entity"]}.{action["key"]}'
            assert action["entity"] in entities, f"{aid}: missing action owning entity"
            assert action["phase"] in phases or action["phase"] == "*", f"{aid}: unknown phase"
            assert (
                action["trigger"] != "hook" or action.get("hook") in hooks
            ), f'{aid}: unknown hook {action.get("hook")}'
            assert action["trigger"] != "command" or not action.get(
                "hook"
            ), f"{aid}: command unexpectedly has hook"
            assert (action["entity"], action["key"]) not in action_keys, f"{aid}: duplicate action"
            action_keys.add((action["entity"], action["key"]))
            assert bool(action.get("iterator")) == bool(
                action.get("variable")
            ), f"{aid}: incomplete iterator"
            parameters = {p["key"] for p in action.get("parameters", [])}
            for node in walk(action):
                if not isinstance(node, dict):
                    continue
                op = node.get("op")
                if op is not None:
                    counts["operators"].add(op)
                    info = operator_registry.get(op)
                    assert (
                        info and info.get("status") == "specified"
                    ), f"{aid}: operator {op!r} not specified"
                    if isinstance(node.get("args"), dict):
                        observed = {k for k in node["args"]}
                        expected = [set(sig["keys"]) for sig in info.get("observed_signatures", [])]
                        assert (
                            observed in expected
                        ), f"{aid}: invalid signature for {op}: {observed}"
                if op == "context" and str(node.get("ref", "")).startswith("argument."):
                    arg = node["ref"].split(".", 1)[1]
                    assert arg in parameters, f"{aid}: unbound action argument {arg}"
                if op == "entity_by_seed":
                    key = node.get("args", {}).get("key", {}).get("value")
                    assert key in seeds, f"{aid}: unknown seed lookup {key}"
                if op == "field":
                    args = node.get("args", {})
                    if (
                        args.get("entity", {}).get("op") == "context"
                        and args["entity"].get("ref") == "self"
                    ):
                        f = args.get("key", {}).get("value")
                        assert (
                            action["entity"],
                            f,
                        ) in field_map, f"{aid}: undeclared field self.{f}"
            counts["actions"] += 1
        counts["games"] += 1
        counts["seeds"] += len(seeds)
    # Each operator belongs to one well-defined generic category; no game name can be a primitive key.
    assert not any(
        any(game in key for game in GAME_KEYS) for key in counts["operators"]
    ), "game-specific operator in registry"
    return counts


def main() -> None:
    counts = validate_data()
    assert counts["games"] == 4 and counts["actions"] == 72, counts
    prisma = (ROOT / "packages/server/supabase/schema.prisma").read_text()
    sql = (ROOT / "packages/server/supabase/integrity.sql").read_text()
    models = re.findall(r"^model (\w+) \{", prisma, re.MULTILINE)
    assert len(models) == 38 and len(set(models)) == 38, "expected 38 Prisma models"
    assert "CREATE TRIGGER participant_capacity_guard" in sql, "seat capacity unguarded"
    assert "CREATE TRIGGER game_target_size_guard" in sql, "lobby target unguarded"
    print(
        f"PASS: {counts['games']} data definitions, {counts['actions']} actions, "
        f"{len(counts['operators'])} referenced operator kinds, {len(models)} models"
    )
    print("NOT VERIFIED: SQL migrations, API behavior, real identities or gameplay.")


if __name__ == "__main__":
    main()
