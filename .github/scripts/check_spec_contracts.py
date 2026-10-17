#!/usr/bin/env python3
"""Check Mermaid design completeness, not runtime or deployed database behavior."""

from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRD = ROOT / ".agents/PRD.md"
DIAGRAMS = ROOT / ".agents/requirements/diagrams"
NAMES = (
    "engine_uml",
    "client_uml",
    "api",
    "api_dtos",
    "database",
    "integrity",
    "configuration_schema",
    "operators",
    "chess",
    "english-draughts",
    "international-draughts",
    "moneyproperty",
)


def get(name: str) -> str:
    path = DIAGRAMS / (name + ".mmd")
    assert path.is_file(), f"missing normative design graph: {path}"
    text = path.read_text(encoding="utf-8")
    assert text.startswith(("flowchart ", "erDiagram", "classDiagram", "sequenceDiagram")), path
    assert len(text.splitlines()) > 10, f"incomplete graph: {name}"
    return text


def nodes(body: str, prefix: str) -> int:
    return len(re.findall(r"^\s*" + prefix + r"\d+\[", body, flags=re.MULTILINE))


def main() -> None:
    prd = PRD.read_text(encoding="utf-8")
    graph = {name: get(name) for name in NAMES}
    for name in NAMES:
        assert f"(requirements/diagrams/{name}.mmd)" in prd, f"unlinked diagram {name}"
    assert nodes(graph["api"], "api") == 33, "33 HTTP operation references required"
    assert nodes(graph["api_dtos"], "dto") == 28, "28 API DTOs required"
    assert nodes(graph["operators"], "op") == 101, "101 typed operators required"
    er = graph["database"]
    tables = re.findall(r"^\s+([a-z][a-z0-9_]*)\s+\{$", er, flags=re.MULTILINE)
    assert len(tables) == 39 and len(set(tables)) == 39, "38 tables + external auth projection"
    relations = re.findall(r"^\s+\w+\s+\|\|--o[\{\|]\s+\w+\s+:", er, flags=re.MULTILINE)
    assert (
        len(relations) == 75
    ), f"expected 74 in-schema references plus Auth projection, found {len(relations)}"
    for name, count in (
        ("chess", 24),
        ("english-draughts", 9),
        ("international-draughts", 9),
        ("moneyproperty", 30),
    ):
        assert nodes(graph[name], "a") == count, f"{name} action topology truncated"
        assert "def[" in graph[name], f"{name} lacks a game root"
    assert nodes(graph["integrity"], "trig") >= 8, "SQL-specific guards incomplete"
    assert "participant" in graph["engine_uml"].lower()
    assert "Realtime" in graph["client_uml"]
    # Implementation branches may add SQL/Prisma/JSON; this check validates the
    # shared design diagrams only. Runtime/provider gates must execute separately.
    assert "Lossless conformance gate" in prd, "semantic limitations must be declared"
    print("PASS: 12 Mermaid design diagrams, 33 operations, 28 DTOs, 38 models, 101 operators")
    print("NOT VERIFIED: deployed APIs, game JSON, runtime operators, migrations, RLS or gameplay")


if __name__ == "__main__":
    main()
