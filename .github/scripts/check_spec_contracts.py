#!/usr/bin/env python3
"""Cross-validate the canonical architecture contracts without implementing gameplay.

Checks source inventory and typed dependency connectivity; parseable Prisma models and
relations; SQL table/column consistency; local OpenAPI references and portable JSON Schema
identity; four complete structural built-ins with declared hooks and generic operators.
The checker does NOT certify executable game behavior or live PostgreSQL security.
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]
REQ = ROOT / ".agents/notes/requirements"
DATA = ROOT / "data"
API = ROOT / "packages/server/api/openapi.yaml"
PRISMA = ROOT / "packages/server/supabase/schema.prisma"
INTEGRITY = ROOT / "packages/server/supabase/integrity.sql"
GAME_KEYS = ("chess", "english-draughts", "international-draughts", "moneyproperty")


def fail(message: str) -> None:
    """Stop on first broken normative reference with a specific diagnostic."""
    raise AssertionError(message)


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
    hooks = set(re.findall(r"\('([a-z_]+(?:\.[a-z_]+)+)',\s*\d+", (DATA / "seed.sql").read_text()))
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


def validate_openapi() -> int:
    """Verify OpenAPI references and exact portable schema equivalence."""
    api = yaml.safe_load(API.read_text())
    assert str(api["openapi"]).startswith("3.1."), "OpenAPI version"
    assert api["servers"][0]["url"] == "/api/v1", "API base route"
    for node in walk(api):
        if isinstance(node, dict) and "$ref" in node:
            target = node["$ref"]
            assert target.startswith("#/"), f"external/unresolved API ref {target}"
            ptr = api
            for part in target[2:].split("/"):
                key = part.replace("~1", "/").replace("~0", "~")
                assert isinstance(ptr, dict) and key in ptr, f"API ref unresolved: {target}"
                ptr = ptr[key]
    schema = json.loads((DATA / "configuration.schema.json").read_text())
    embedded = api["components"]["schemas"]["ConfigDocument"]

    def portable_ref(v):
        if isinstance(v, dict):
            return {
                k: (
                    val.replace("#/components/schemas/ConfigDocument/", "#/")
                    if k == "$ref" and isinstance(val, str)
                    else portable_ref(val)
                )
                for k, val in v.items()
            }
        if isinstance(v, list):
            return [portable_ref(x) for x in v]
        return v

    assert portable_ref(embedded) == {
        k: v for k, v in schema.items() if k not in ("$schema", "$id")
    }, "OpenAPI ConfigDocument drifted from JSON Schema"
    operations = [
        (path, method, obj.get("operationId"))
        for path, verbs in api["paths"].items()
        for method, obj in verbs.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    ids = [op for _, _, op in operations]
    assert len(ids) == len(set(ids)) and all(ids), "duplicate or missing OpenAPI operationId"
    return len(ids)


def validate_prisma_sql() -> tuple[int, int]:
    """Verify PSL relations and SQL-owned CHECK/trigger targets against actual model columns."""
    source = PRISMA.read_text()
    models = {}
    for m in re.finditer(r"(?m)^model (\w+) \{([\s\S]*?)^\}", source):
        key, body = m.groups()
        assert key not in models, f"duplicate Prisma model {key}"
        db = re.search(r'@@map\("([^\"]+)"\)', body)
        assert db and '@@schema("bgwq")' in body, f"Prisma model missing PostgreSQL mapping {key}"
        columns = {}
        for line in body.splitlines():
            if not line.startswith("  ") or line.strip().startswith(("/", "@")):
                continue
            p = line.strip().split()
            if len(p) >= 2:
                attr = re.search(r'@map\("([^\"]+)"\)', line)
                columns[p[0]] = (attr.group(1) if attr else p[0], p[1], line)
        models[key] = (db.group(1), columns, body)
    assert len(models) == 38, f"Prisma model count drifted: {len(models)} (expected 38)"
    tablemap = {t: fields for _, (t, fields, _) in models.items()}
    for name, (_, fields, body) in models.items():
        assert len(fields) == len(set(fields)), f"duplicate Prisma field in {name}"
        for line in body.splitlines():
            if "@relation(" in line:
                parts = line.strip().split()
                target = parts[1].removesuffix("[]").removesuffix("?")
                assert target in models, f"Prisma {name}: relation to undefined {target}"
                mo = re.search(r"fields:\s*\[([^\]]+)\],\s*references:\s*\[([^\]]+)\]", line)
                if mo:
                    srcfields = [x.strip() for x in mo.group(1).split(",")]
                    refs = [x.strip() for x in mo.group(2).split(",")]
                    assert len(srcfields) == len(refs), f"Prisma {name}: composite FK mismatch"
                    for f in srcfields:
                        assert f in fields, f"Prisma {name}: FK local field {f}"
                    for f in refs:
                        assert f in models[target][1], f"Prisma {name}: FK target {target}.{f}"
        for match in re.finditer(r"@@(?:id|unique|index)\(\[([^\]]+)\]", body):
            for fld in match.group(1).split(","):
                f = fld.strip().split("(")[0]
                assert f in fields, f"Prisma {name}: index on unknown {f}"
    sql = INTEGRITY.read_text()
    for tbl in re.findall(r'ALTER TABLE bgwq\."(\w+)"', sql):
        assert tbl in tablemap, f"INTEGRITY.sql: unknown table {tbl}"
    # A CHECK constraint is authored against a single table; every quoted column must exist.
    for m in re.finditer(
        r'ALTER TABLE bgwq\."(\w+)" ADD CONSTRAINT "(\w+)" CHECK \(([^;]+?)\);', sql
    ):
        table, check, expression = m.groups()
        known = {db for db, _, _ in tablemap[table].values()}
        for col in re.findall(r'"(\w+)"', expression):
            assert col in known, f"INTEGRITY.sql: {table}.{check} uses unknown column {col}"
    # Published rows cannot be moved out of a frozen version.
    assert (
        "THEN NEW.version_id ELSE OLD.version_id" in sql
        and "NEW.version_id IS DISTINCT FROM OLD.version_id" in sql
    ), "immutable published version guard missing OLD/NEW checks"
    assert "CREATE POLICY bgwq_game_broadcast_read" in sql, "Realtime membership policy absent"
    assert (
        "CREATE CONSTRAINT TRIGGER check_game_revision_history" in sql
    ), "committed revision parity absent"
    assert "REFERENCES auth.users(id)" in sql, "Supabase Auth FK constraints absent"
    return len(models), len(re.findall(r'ADD CONSTRAINT "\w+" CHECK', sql))


def validate_mermaid() -> tuple[int, int]:
    """Verify exact tree alignment, typed connections, and no hidden game-action AST nodes."""
    ast = (REQ / "AST.mmd").read_text()
    assert ast.startswith("flowchart TB\n"), "expected plain Mermaid, not Markdown"
    assert "reference_AST.svg" not in ast, "tracked SVG still referenced"
    nodes = {}
    for m in re.finditer(r'(?m)^\s*(F\d+)\["([^"\n]*)"\]\s*$', ast):
        assert m.group(1) not in nodes, "duplicate Mermaid declaration"
        nodes[m.group(1)] = m.group(2).split("<br/>", 1)[0]
    assert len(nodes) >= 140, f"Mermaid declarations missing: {len(nodes)}"
    declarations = re.findall(r'(?m)^\s*D\d+\["([^"\n]*)"\]\s*
    assert len(names) == len(nodes), "source file declared twice"
    arch = (REQ / "ARCHITECTURE.md").read_text()
    block = re.search(r"```text\n([\s\S]*?)\n```", arch)
    assert block, "ARCHITECTURE missing source tree"
    paths = set()
    stack = []
    for line in block.group(1).splitlines():
        if not line.strip():
            continue
        text = line.split("  # ", 1)[0].rstrip()
        indent = len(text) - len(text.lstrip(" "))
        depth = indent // 2
        stack = stack[:depth]
        name = text.strip()
        if name.endswith("/"):
            stack.append(name.rstrip("/"))
        else:
            assert "  # " in line, f"inline source doc missing for {name}"
            paths.add("/".join(stack + [name]))
    assert (
        paths == names
    ), f"inventory drift: missing AST {sorted(paths-names)[:6]}, missing tree {sorted(names-paths)[:6]}"
    pattern = re.compile(r"(?m)^\s*(F\d+)\s+-->\|([^|]+)\|\s*(F\d+)\s*$")
    edges = pattern.findall(ast)
    assert len(edges) >= len(nodes) - 1, "Mermaid lacks source relationships"
    neighbors = {n: set() for n in nodes}
    for a, label, b in edges:
        assert a in nodes and b in nodes, "edge to undefined source file"
        assert label.strip() and not label.strip().lower().startswith(
            "connect"
        ), "untyped or synthetic dependency edge"
        neighbors[a].add(b)
        neighbors[b].add(a)
    isolated = [n for n, v in neighbors.items() if not v]
    assert not isolated, f"isolated source modules {isolated}"
    todo = [next(iter(nodes))]
    seen = set(todo)
    while todo:
        for n in neighbors[todo.pop()] - seen:
            seen.add(n)
            todo.append(n)
    assert len(seen) == len(nodes), f"disconnected source graph: {sorted(set(nodes)-seen)}"
    # The AST encodes implementation-level declarations only; portable rules are in JSON.
    assert not re.search(r"(?m)^\s*[A-Z]\d+_\w+\[", ast), "non-source game action AST"
    return len(nodes), len(edges)


def main() -> None:
    """Run all independent contract checks as a CI gate."""
    for expected in (API, PRISMA, INTEGRITY, DATA / "configuration.schema.json",
                     DATA / "operators.json", REQ / "AST.mmd", REQ / "ARCHITECTURE.md"):
        assert expected.is_file(), f"Missing authoritative contract {expected}"
    for obsolete in (REQ / "data", REQ / "SCHEMA.prisma", REQ / "INTEGRITY.sql",
                     REQ / "API.yaml", REQ / "diagrams/reference_AST.svg"):
        assert not obsolete.exists(), f"Superseded or generated contract was retained: {obsolete}"
    # Links in the canonical product and source-tree docs must resolve in the
    # checked-out repository; a folder move must not leave dead references.
    for md in (ROOT / ".agents/PRD.md", REQ / "ARCHITECTURE.md"):
        body = md.read_text()
        for href in re.findall(r"\\[[^\\]]+\\]\\(([^)]+)\\)", body):
            if href.startswith(("http:", "https:", "#", "mailto:")):
                continue
            target = href.split("#", 1)[0]
            assert (md.parent / target).exists(), f"{md.relative_to(ROOT)}: broken link {href}"
    assert "37-model relational declaration" not in (REQ / "ARCHITECTURE.md").read_text(), "obsolete Prisma model count"
    diagram = (REQ / "AST.mmd").read_text()
    assert "Validate typed inputs; compute" not in diagram, "vague method contracts"
    assert "implementation defined by owning source" not in diagram, "missing behavior contracts"
    assert not (REQ / "data").exists(), "duplicate portable data"
    assert not (REQ / "SCHEMA.prisma").exists(), "duplicate schema"
    assert not (REQ / "API.yaml").exists(), "duplicate API contract"
    assert not (REQ / "diagrams" / "reference_AST.svg").exists(), "tracked SVG not permitted"
    games = validate_data()
    http = validate_openapi()
    models, checks = validate_prisma_sql()
    files, edges = validate_mermaid()
    print(
        f'PASS: {games["games"]} games, {games["seeds"]} seeds, {games["actions"]} actions, {len(games["operators"])} declared operators'
    )
    print(f"PASS: {http} OpenAPI operations and exact portable schema projection")
    print(f"PASS: {models} Prisma models, {checks} SQL CHECK constraints and cross-references")
    print(f"PASS: {files} source declarations / {edges} typed Mermaid relationships; all connected")
    print(
        "NOT VERIFIED: actual Prisma validation/migrations, execution of games, browser/native deployment or runtime code generation"
    )


if __name__ == "__main__":
    main()
, ast)
    assert len(declarations) >= 100, f"Missing source function declarations: {len(declarations)}"
    assert not any("implementation defined by owning source" in d for d in declarations), "Placeholder source-function contracts"
    source_paths = set(nodes.values())
    for declaration in declarations:
        owner = declaration.split("<br/>", 1)[0]
        assert owner in source_paths, f"Orphan source declaration: {owner}"
        assert "Algorithm:" in declaration, f"No algorithm specification for: {owner}"
    names = set(nodes.values())
    assert len(names) == len(nodes), "source file declared twice"
    arch = (REQ / "ARCHITECTURE.md").read_text()
    block = re.search(r"```text\n([\s\S]*?)\n```", arch)
    assert block, "ARCHITECTURE missing source tree"
    paths = set()
    stack = []
    for line in block.group(1).splitlines():
        if not line.strip():
            continue
        text = line.split("  # ", 1)[0].rstrip()
        indent = len(text) - len(text.lstrip(" "))
        depth = indent // 2
        stack = stack[:depth]
        name = text.strip()
        if name.endswith("/"):
            stack.append(name.rstrip("/"))
        else:
            assert "  # " in line, f"inline source doc missing for {name}"
            paths.add("/".join(stack + [name]))
    assert (
        paths == names
    ), f"inventory drift: missing AST {sorted(paths-names)[:6]}, missing tree {sorted(names-paths)[:6]}"
    pattern = re.compile(r"(?m)^\s*(F\d+)\s+-->\|([^|]+)\|\s*(F\d+)\s*$")
    edges = pattern.findall(ast)
    assert len(edges) >= len(nodes) - 1, "Mermaid lacks source relationships"
    neighbors = {n: set() for n in nodes}
    for a, label, b in edges:
        assert a in nodes and b in nodes, "edge to undefined source file"
        assert label.strip() and not label.strip().lower().startswith(
            "connect"
        ), "untyped or synthetic dependency edge"
        neighbors[a].add(b)
        neighbors[b].add(a)
    isolated = [n for n, v in neighbors.items() if not v]
    assert not isolated, f"isolated source modules {isolated}"
    todo = [next(iter(nodes))]
    seen = set(todo)
    while todo:
        for n in neighbors[todo.pop()] - seen:
            seen.add(n)
            todo.append(n)
    assert len(seen) == len(nodes), f"disconnected source graph: {sorted(set(nodes)-seen)}"
    # The AST encodes implementation-level declarations only; portable rules are in JSON.
    assert not re.search(r"(?m)^\s*[A-Z]\d+_\w+\[", ast), "non-source game action AST"
    return len(nodes), len(edges)


def main() -> None:
    """Run all independent contract checks as a CI gate."""
    games = validate_data()
    http = validate_openapi()
    models, checks = validate_prisma_sql()
    files, edges = validate_mermaid()
    print(
        f'PASS: {games["games"]} games, {games["seeds"]} seeds, {games["actions"]} actions, {len(games["operators"])} declared operators'
    )
    print(f"PASS: {http} OpenAPI operations and exact portable schema projection")
    print(f"PASS: {models} Prisma models, {checks} SQL CHECK constraints and cross-references")
    print(f"PASS: {files} source declarations / {edges} typed Mermaid relationships; all connected")
    print(
        "NOT VERIFIED: actual Prisma validation/migrations, execution of games, browser/native deployment or runtime code generation"
    )


if __name__ == "__main__":
    main()
