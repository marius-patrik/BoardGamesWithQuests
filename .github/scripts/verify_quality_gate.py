"""Fail-closed repository acceptance of pinned DarkFactory quality reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

# Supplemental browser/provider acceptance remains a separate product release gate.
REQUIRED = {
    **{
        ("python", ".", "test", version): {"pytest", "pytest -q"}
        for version in ("3.10", "3.11", "3.12", "3.13")
    },
    ("python", ".", "format_check", ""): {"black --check --line-length 100 ."},
    ("rust", "packages/desktop/src-tauri", "test", ""): {"cargo test --all-features --workspace"},
    ("rust", "packages/desktop/src-tauri", "lint", ""): {
        "cargo clippy --workspace --all-targets --all-features -- -D warnings"
    },
    ("rust", "packages/desktop/src-tauri", "format_check", ""): {"cargo fmt --all -- --check"},
    ("node", "packages/web", "typecheck", ""): {"bun run typecheck"},
    ("node", "packages/web", "lint", ""): {"biome lint ."},
    ("node", "packages/web", "format_check", ""): {"biome ci ."},
}


def read_object(path: Path) -> dict[str, Any]:
    """Read one JSON object, rejecting missing or malformed report files.

    Args:
        path: Report path.

    Returns:
        Decoded object.

    Raises:
        ValueError: Report does not contain an object.
    """

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        """Reject duplicate report fields rather than silently discarding evidence."""
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate report field: {key}")
            result[key] = value
        return result

    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(data, dict):
        raise ValueError(f"report must be an object: {path}")
    return data


def validate_plan(plan: dict[str, Any], repo: Path) -> list[str]:
    """Require genuine executable checks for every repository quality scope.

    Args:
        plan: Pinned DarkFactory matrix report.
        repo: Repository containing the permanent Python behavior suite.

    Returns:
        Unique identifiers of all detected executable actions.

    Raises:
        ValueError: Mandatory discovery, command or test-suite evidence is absent.
    """
    matrix, gaps = plan.get("matrix"), plan.get("gaps")
    if not isinstance(matrix, list) or not matrix or not isinstance(gaps, list):
        raise ValueError("nonempty quality matrix and gap array are required")
    if not any((repo / "tests").glob("test_*.py")):
        raise ValueError("permanent Python behavioral tests were not discovered")
    seen: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    identifiers: list[str] = []
    for entry in matrix:
        if not isinstance(entry, dict):
            raise ValueError("quality matrix entry must be an object")
        identifier, command = entry.get("id"), entry.get("command")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            raise ValueError("quality action identifiers must be nonempty and unique")
        if not isinstance(command, str) or not command.strip():
            raise ValueError(f"quality action has no executable command: {identifier}")
        identity = tuple(entry.get(key, "") for key in ("ecosystem", "cwd", "kind", "version"))
        if any(not isinstance(value, str) for value in identity):
            raise ValueError("quality scope fields must be strings")
        if identity in seen:
            raise ValueError(f"duplicate quality scope: {identity}")
        seen[identity] = entry
        identifiers.append(identifier)
    for identity, commands in REQUIRED.items():
        entry = seen.get(identity)
        if entry is None:
            raise ValueError(f"missing mandatory quality action: {identity}")
        if entry["command"] not in commands:
            raise ValueError(f"unsupported mandatory command: {identity}")
    for gap in gaps:
        if (
            not isinstance(gap, dict)
            or not isinstance(gap.get("packageId"), str)
            or gap.get("kind") not in {"test", "lint", "format_check", "typecheck"}
        ):
            raise ValueError("quality gap must identify a package")
        package = gap["packageId"]
        for ecosystem, cwd, kind, _ in REQUIRED:
            if package == f"{ecosystem}:{cwd}" and gap.get("kind") == kind:
                raise ValueError(f"mandatory action reported as unsupported: {package} {kind}")
    return identifiers


def validate_results(identifiers: list[str], results: Path) -> None:
    """Require a successful execution report for every detected matrix action.

    Args:
        identifiers: Expected action identifiers from the validated plan.
        results: Downloaded same-run action-artifact directory.

    Raises:
        ValueError: Reports are absent, duplicated, unexpected or unsuccessful.
    """
    observed: dict[str, str] = {}
    for path in results.rglob("result.json"):
        report = read_object(path)
        if set(report) != {"id", "result"}:
            raise ValueError("execution report requires exactly id and result")
        identifier = report["id"]
        if (
            not isinstance(identifier, str)
            or identifier not in identifiers
            or identifier in observed
        ):
            raise ValueError("unexpected or duplicate execution report")
        observed[identifier] = report["result"]
    for identifier in identifiers:
        if observed.get(identifier) != "success":
            raise ValueError(f"quality action did not execute successfully: {identifier}")


def main() -> int:
    """Validate discovery/execution or record one runner's actual job result.

    Returns:
        Zero for accepted evidence; one for missing or rejected evidence.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--results", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--id")
    parser.add_argument("--result")
    args = parser.parse_args()
    try:
        if args.record is not None:
            if not args.id or args.result not in {"success", "failure", "cancelled", "skipped"}:
                raise ValueError("record requires an action id and recognized job result")
            args.record.write_text(
                json.dumps({"id": args.id, "result": args.result}), encoding="utf-8"
            )
        else:
            if args.plan is None:
                raise ValueError("quality plan is required")
            plan = read_object(args.plan)
            identifiers = validate_plan(plan, args.repo)
            if args.results is not None:
                validate_results(identifiers, args.results)
            print(
                f"Accepted {len(identifiers)} quality actions; additional gaps: {len(plan['gaps'])}."
            )
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"Quality gate rejected: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
