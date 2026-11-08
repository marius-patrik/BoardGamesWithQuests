#!/usr/bin/env python3
"""Validate the cleanroom repository layout without regenerating canonical documents.

PRD and AGENTS are authored sources, never projections of old notes/rules records.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / ".agents"
DOCS = ROOT / "docs"

OBSOLETE_DIRECTORIES = (
    "packages",
    ".agents/architecture",
    ".agents/reference",
    ".agents/decisions",
    ".agents/notes",
    ".agents/rules",
)
OBSOLETE_DOCUMENTS = (
    ".agents/ARCHITECTURE.md",
    ".agents/GOAL.md",
    ".agents/PLAN.md",
    ".agents/README.md",
    ".agents/TODO.md",
    ".agents/SCRATCHPAD.md",
)


def validate_layout() -> list[str]:
    """Report issues; do not mutate developer files or release configuration."""
    errors: list[str] = []
    for folder in (AGENTS, DOCS, ROOT / ".github", ROOT / "src"):
        if not folder.is_dir() or folder.is_symlink():
            errors.append(f"Expected real directory: {folder.relative_to(ROOT)}")
    for name, target in (
        ("README.md", ".agents/PRD.md"),
        ("CONTRIBUTING.md", ".agents/AGENTS.md"),
    ):
        link = ROOT / name
        # Git for Windows may materialize a tracked 120000 symlink as text.
        # Verify its content there, and require real links on POSIX.
        tracked_link = link.is_symlink() and link.readlink().as_posix() == target
        windows_link = (
            sys.platform == "win32"
            and not link.is_symlink()
            and link.is_file()
            and link.read_text(encoding="utf-8").strip() == target
        )
        if not (tracked_link or windows_link):
            errors.append(f"{name} must be a symlink to {target}")
    for name in ("PRD.md", "AGENTS.md"):
        if not (AGENTS / name).is_file():
            errors.append(f"Missing canonical authored document: .agents/{name}")
    for old in OBSOLETE_DIRECTORIES + OBSOLETE_DOCUMENTS:
        if (ROOT / old).exists():
            errors.append(f"Obsolete layout path: {old}")
    for package in ("model", "view", "controller"):
        if (ROOT / package).exists():
            errors.append(f"Shadow Python package outside src/: {package}/")
        if not (ROOT / "src" / package / "__init__.py").is_file():
            errors.append(f"Missing production package: src/{package}/")
    expected = {
        "docs/architecture/diagrams/ast.mmd",
        "docs/architecture/diagrams/uml.mmd",
        "docs/reference/diagrams/mvc.mmd",
        "docs/reference/diagrams/uml.mmd",
        "docs/reference/images/GUI_mockup.svg",
    }
    for path in sorted(expected):
        if not (ROOT / path).is_file():
            errors.append(f"Missing documentation asset: {path}")
    if not (ROOT / ".darkfactory/installation.json").is_file():
        errors.append("Missing installed DarkFactory integration metadata")
    for path in sorted((AGENTS / "agents").glob("*.md")) + sorted(
        (AGENTS / "skills").glob("*/SKILL.md")
    ):
        header = path.read_text(encoding="utf-8")
        if not re.match(r"\A---\nname: [a-z0-9-]+\ndescription: .+\n---\n", header):
            errors.append(f"Invalid agent metadata: {path.relative_to(ROOT)}")
    try:
        config = json.loads((ROOT / "repo.dfconfig").read_text(encoding="utf-8"))
        if config["repo"]["identity"]["repo"] != "BoardGamesWithQuests":
            errors.append("repo.dfconfig identity does not match this repository")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Invalid repo.dfconfig: {exc}")

    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--cached"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if tracked.returncode:
        errors.append("Unable to inspect tracked files: " + tracked.stderr.decode(errors="replace"))
    else:
        for name in filter(
            None, tracked.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        ):
            parts = name.split("/")
            if name.startswith("packages/") or name.startswith(".agents/architecture/"):
                errors.append(f"Obsolete tracked content: {name}")
            if name.startswith(".github/tests/"):
                continue
            leaf = parts[-1]
            if any(
                segment.lower() in {"tests", "test", "fixtures", "__tests__"}
                for segment in parts[:-1]
            ):
                errors.append(f"Tests or fixtures must be under .github/tests/: {name}")
            if leaf.startswith(("test_", "test-")) or re.search(
                r"(?i)(?:[._-]test|[._-]spec|[._-]e2e)\.[^.]+$", leaf
            ):
                errors.append(f"Test file outside .github/tests/: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    errors = validate_layout()
    for error in errors:
        print("error: " + error, file=sys.stderr)
    if not errors:
        print("Cleanroom repository, canonical documents, and docs asset layout verified.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
