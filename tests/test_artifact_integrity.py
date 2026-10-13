"""Verify that active specifications resolve and stay free of status narratives."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    "README.md",
    ".agents/AGENTS.md",
    ".agents/SCRATCHPAD.md",
    ".agents/notes/PLAN.md",
    ".agents/notes/PRD.md",
    ".agents/notes/object_model.md",
    ".agents/notes/json_contract.md",
    ".agents/notes/chess_rules.md",
    ".agents/notes/reference_diagram.md",
    "packages/server/README.md",
    "packages/web/README.md",
    "packages/desktop/README.md",
]
CHRONOLOGY = re.compile(
    r"\b(?:historical|legacy|retired|superseded|formerly|previously|currently|current|original|obsolete)\b",
    flags=re.IGNORECASE,
)


def test_documents_define_interfaces_without_chronology() -> None:
    offending = []
    for relative in DOCS:
        for line_number, line in enumerate((ROOT / relative).read_text("utf-8").splitlines(), 1):
            if CHRONOLOGY.search(line):
                offending.append(f"{relative}:{line_number}")
    assert not offending, "time-dependent narratives: " + ", ".join(offending)


def test_markdown_navigation_links_point_to_existing_artifacts() -> None:
    broken = []
    for relative in DOCS:
        source = ROOT / relative
        for target in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", source.read_text("utf-8")):
            destination = target.split("#", 1)[0]
            if not destination or "://" in destination:
                continue
            if not (source.parent / destination).resolve().exists():
                broken.append(f"{relative}: {destination}")
    assert not broken, "broken documentation links: " + "; ".join(broken)


def test_contribution_rules_cannot_become_an_independent_copy() -> None:
    contributing = ROOT / "CONTRIBUTING.md"
    assert contributing.is_symlink()
    assert contributing.resolve() == (ROOT / ".agents/AGENTS.md").resolve()
