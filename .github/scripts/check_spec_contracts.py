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
REQ = ROOT / ".agents/requirements"
DATA = ROOT / ".agents/reference/data"
API = REQ / "notes/API.md"
PRISMA = ROOT / "packages/server/supabase/schema.prisma"
INTEGRITY = ROOT / ".agents/reference/notes/integrity.sql"
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
    hooks = set(re.findall(r"\('([a-z_]+(?:\.[a-z_]+)+)',\s*\d+", (ROOT / "packages/server/supabase/migrations/seed.sql").read_text()))
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


def embedded_openapi() -> dict:
    """Parse the unique normative OpenAPI YAML block inside requirements/notes/API.md."""
    text = API.read_text(encoding="utf-8")
    blocks = re.findall(r"(?ms)^\x60{3}yaml\n(.*?)\n\x60{3}\s*$", text)
    assert len(blocks) == 1, "API.md must contain exactly one extractable YAML contract"
    doc = yaml.safe_load(blocks[0])
    assert isinstance(doc, dict), "invalid canonical OpenAPI contract"
    return doc


def op_owners() -> dict[str, str]:
    """Read the complete one-owner-per-operation matrix, not a loose route count."""
    source = (REQ / "notes/CONTRACTS.md").read_text(encoding="utf-8")
    owned = re.findall(r"(?m)^\| \x60([a-zA-Z][a-zA-Z0-9]+)\x60 \| ([^|]+) \|", source)
    registry: dict[str, str] = {}
    for operation, owner in owned:
        assert operation not in registry, f"duplicate HTTP owner: {operation}"
        assert owner.strip(), f"owner not declared for {operation}"
        registry[operation] = owner.strip()
    assert registry, "no API operation ownership matrix"
    return registry


def validate_openapi() -> int:
    """Verify OpenAPI references and exact portable schema equivalence."""
    api = embedded_openapi()
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
    for component in ("GameCreate", "Game", "GameSummary", "Invitation"):
        shape = api["components"]["schemas"][component]
        assert "target_participants" in shape["required"], f"{component} missing fixed capacity"
        assert shape["properties"]["target_participants"]["minimum"] >= 2
    session = api["paths"]["/session"]["get"]
    assert session["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/Session"
    )
    assert "anonymous CSRF cookie" in API.read_text(), "anonymous login bootstrap is unspecified"
    operations = [
        (path, method, obj.get("operationId"))
        for path, verbs in api["paths"].items()
        for method, obj in verbs.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    ids = [op for _, _, op in operations]
    assert len(ids) == len(set(ids)) and all(ids), "duplicate or missing OpenAPI operationId"
    for route, method, operation in operations:
        assert (
            operation in op_owners()
        ), f"HTTP operation lacks an owned persistence/service boundary: {operation}"
        if method != "get":
            params = api["paths"][route][method].get("parameters", [])
            assert any(
                x.get("$ref", "").endswith("/csrf") for x in params
            ), f"{operation}: mutation must declare CSRF parameter"
        assert api["paths"][route][method].get(
            "responses"
        ), f"{operation}: missing response contract"
    assert set(ids) == set(op_owners()), "HTTP operation ownership matrix disagrees with API paths"
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
    assert "CREATE TRIGGER game_target_size_guard" in sql, "reference SQL omits bounded lobby target"
    assert (
        "CREATE TRIGGER participant_capacity_guard" in sql and "FOR UPDATE OF g" in sql
    ), "concurrent joins lack enforced variable seat capacity"
    return len(models), len(re.findall(r'ADD CONSTRAINT "\w+" CHECK', sql))


def validate_diagrams() -> tuple[int, int]:
    """Validate actual Mermaid syntax and target interface connectivity, not a synthetic full source AST."""
    engine = (REQ / "diagrams/engine_uml.mmd").read_text(encoding="utf-8")
    client = (REQ / "diagrams/client_uml.mmd").read_text(encoding="utf-8")
    assert engine.startswith("classDiagram\n"), "engine UML must be a Mermaid class diagram"
    assert client.startswith("sequenceDiagram\n"), "client UML must be a Mermaid sequence diagram"
    classes = set(re.findall(r"(?m)^class (\w+) \{", engine))
    assert len(classes) >= 15, "target engine omits principal interfaces"
    edges = re.findall(
        r'(?m)^(\w+)(?: "[^"]+")?\s+(?:-->|o--|<\|--)(?: "[^"]+")?\s+(\w+)\s*:', engine
    )
    assert len(edges) >= len(classes) - 1, "target engine lacks typed relationships"
    graph = {name: set() for name in classes}
    for src, dst in edges:
        assert src in classes and dst in classes, f"undefined engine UML endpoint: {src} -> {dst}"
        graph[src].add(dst)
        graph[dst].add(src)
    visited = {"GameService"}
    todo = ["GameService"]
    while todo:
        for target in graph[todo.pop()] - visited:
            visited.add(target)
            todo.append(target)
    assert visited == classes, f"disconnected engine interfaces: {sorted(classes - visited)}"
    assert "Chess" not in " ".join(classes) and "MoneyProperty" not in " ".join(
        classes
    ), "game-specific interpreter class"
    for semantic in (
        "expected_revision",
        "idempotency_key",
        "request_digest",
        "min_participants",
        "max_participants",
    ):
        assert semantic in engine, f"engine UML lacks {semantic} contract"
    api = embedded_openapi()
    for path in re.findall(r"(?:GET|POST|PUT|PATCH|DELETE) (/[^\s()]+)", client):
        canonical = re.sub(r"\{id\}", "{gameId}", path)
        assert (
            canonical in api["paths"]
        ), f"client flow references uncontracted HTTP endpoint {path}"
    assert (
        "reconnect" in client.lower() and "Stale revision" in client
    ), "recovery and concurrency path missing"
    # Original references are authored, and implementation diagrams are generated;
    # none of them is allowed to masquerade as an immutable normative source graph.
    for relative in (
        "reference/diagrams/mvc.mmd",
        "reference/diagrams/uml.mmd",
        "architecture/diagrams/ast.mmd",
        "architecture/diagrams/uml.mmd",
    ):
        actual = ROOT / ".agents" / relative
        assert actual.is_file() and actual.suffix == ".mmd", f"missing diagram {relative}"
    assert (
        ROOT / ".agents/reference/images/GUI_mockup.svg"
    ).is_file(), "original GUI reference missing"
    assert not (ROOT / ".agents/notes/diagrams").exists(), "obsolete diagram structure retained"
    assert not (
        ROOT / ".agents/notes/images"
    ).exists(), "obsolete top-level image directory retained"
    # The merged target source tree remains inline in the PRD, with all files
    # annotated, but it is not enforced as fabricated matching source-AST nodes.
    prd = (ROOT / ".agents/PRD.md").read_text(encoding="utf-8")
    target = re.search(r"`{3}text\n([\s\S]*?)\n`{3}", prd)
    assert target, "PRD must own the annotated target source tree"
    for line in target.group(1).splitlines():
        if line.strip() and not line.strip().endswith("/"):
            assert "  # " in line, f"unannotated target declaration: {line}"
    assert "  client/  #" in target.group(1), "client ownership missing"
    assert "  web/  #" not in target.group(1), "obsolete frontend ownership"
    return len(classes), len(edges)


def main() -> None:
    """Check exactly one normative API, canonical persisted identities, and UML dependencies."""
    for required in (
        API,
        PRISMA,
        INTEGRITY,
        DATA / "configuration.schema.json",
        DATA / "operators.json",
        REQ / "diagrams/engine_uml.mmd",
        REQ / "diagrams/client_uml.mmd",
        REQ / "notes/CONTRACTS.md",
    ):
        assert required.is_file(), f"missing authoritative source {required}"
    for stale in (
        "packages/server/api/openapi.yaml",
        ".agents/notes/requirements/AST.mmd",
        ".agents/notes/requirements/ARCHITECTURE.md",
    ):
        assert not (ROOT / stale).exists(), f"obsolete overlapping contract still tracked: {stale}"
    games = validate_data()
    operations = validate_openapi()
    models, checks = validate_prisma_sql()
    classes, relations = validate_diagrams()
    # Intended participant capacity and revision/event ownership must exist across
    # API, relational fields, and runtime contract: one failure blocks the gate.
    prisma = PRISMA.read_text()
    for declaration in (
        "minimumParticipants",
        "maximumParticipants",
        "model Participant",
        "targetParticipants",
        "model ActiveParticipant",
        "model EventMutation",
        "model GameOutcome",
        "model EventValue",
        "model GameEntity",
        "model Rating",
    ):
        assert declaration in prisma, f"missing persisted domain requirement {declaration}"
    assert "CREATE CONSTRAINT TRIGGER check_game_revision_history" in INTEGRITY.read_text()
    assert "auth.uid()" in INTEGRITY.read_text(), "Realtime policy lacks identity-based membership"
    print(f'PASS: {games["games"]} game definitions, {games["actions"]} configured actions')
    print(f"PASS: {operations} owned HTTP operations with local OpenAPI references")
    print(f"PASS: {models} Prisma models, {checks} supplementary reference SQL constraints")
    print(f"PASS: {classes} engine interfaces and {relations} declared UML relationships")
    print(
        "NOT VERIFIED: migration execution, formal engine semantics, real API/DB/browser integration or runtime replay"
    )


if __name__ == "__main__":
    main()
