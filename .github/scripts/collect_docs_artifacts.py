#!/usr/bin/env python3
"""Restore passing documentation snapshots from GitHub Actions artifacts.

The collector reads immutable build artifacts; it never fetches a deployment
branch or executes code from a pull-request checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def gh(*arguments: str) -> str:
    """Invoke the authenticated GitHub CLI without shell interpolation."""
    return subprocess.run(
        ["gh", *arguments],
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def api(route: str) -> Any:
    """Read the GitHub REST response through the workflow's read-only token."""
    return json.loads(gh("api", route))


def pages(route: str) -> list[dict[str, Any]]:
    """Read all GitHub REST pages, rejecting partial collections on errors."""
    items: list[dict[str, Any]] = []
    for page in range(1, 21):
        result = api(f"{route}{'&' if '?' in route else '?'}per_page=100&page={page}")
        if isinstance(result, dict):
            batch = result["artifacts"]
        else:
            batch = result
        items.extend(batch)
        if len(batch) < 100:
            return items
    raise RuntimeError(f"Pagination limit reached for {route}")


def open_same_repo_prs(repo: str) -> dict[int, dict[str, str]]:
    """Retain only PRs whose source is owned by this repository."""
    result: dict[int, dict[str, str]] = {}
    for pr in pages(f"repos/{repo}/pulls?state=open"):
        head = pr["head"]
        if head["repo"] and head["repo"]["full_name"].casefold() == repo.casefold():
            result[int(pr["number"])] = {
                "sha": head["sha"],
                "branch": head["ref"],
            }
    return result


def artifacts(repo: str, name: str) -> list[dict[str, Any]]:
    """Find non-expired uploaded snapshots by the exact artifact name."""
    from urllib.parse import quote

    return [
        item
        for item in pages(f"repos/{repo}/actions/artifacts?name={quote(name, safe='')}")
        if item["name"] == name and not item.get("expired", False)
    ]


def approved_run(
    repo: str,
    artifact: dict[str, Any],
    expected_workflow: str,
    expected_events: set[str],
    expected_branch: str,
) -> int | None:
    """Reject artifacts not produced by the intended successful workflow."""
    run_id = (artifact.get("workflow_run") or {}).get("id")
    if not isinstance(run_id, int):
        return None
    run = api(f"repos/{repo}/actions/runs/{run_id}")
    if (
        run.get("name") != expected_workflow
        or run.get("event") not in expected_events
        or run.get("conclusion") != "success"
        or run.get("head_branch") != expected_branch
        or run.get("repository", {}).get("full_name", "").casefold() != repo.casefold()
    ):
        return None
    return run_id


def download(repo: str, run_id: int, name: str, destination: Path) -> None:
    """Download a named artifact from an authenticated, selected run."""
    destination.mkdir(parents=True)
    gh(
        "run",
        "download",
        str(run_id),
        "--repo",
        repo,
        "--name",
        name,
        "--dir",
        str(destination),
    )


def restore(
    repo: str,
    staging: Path,
    name: str,
    workflow: str,
    events: set[str],
    branch: str,
    expected_sha: str | None = None,
) -> bool:
    """Restore the newest valid snapshot matching the live PR head, if any."""
    for item in artifacts(repo, name):
        run_id = approved_run(repo, item, workflow, events, branch)
        if run_id is None:
            continue
        candidate = staging.parent / f"candidate-{item['id']}"
        if candidate.exists():
            shutil.rmtree(candidate)
        download(repo, run_id, name, candidate)
        if not (candidate / "index.html").is_file():
            shutil.rmtree(candidate)
            continue
        if expected_sha is not None:
            head_file = candidate / ".preview-head"
            if not head_file.is_file() or head_file.read_text().strip() != expected_sha:
                shutil.rmtree(candidate)
                continue
        destination = staging / name.removeprefix("docs-preview-")
        if name == "docs-main":
            # The main artifact may be from the last passing main revision.
            for file in candidate.iterdir():
                target = staging / file.name
                if target.exists():
                    raise ValueError(f"Overlapping main documentation path: {target}")
                shutil.move(str(file), str(target))
        else:
            number = name.removeprefix("docs-preview-")
            if not re.fullmatch(r"[0-9]+", number):
                raise ValueError("Unsafe PR artifact identifier")
            destination = staging / f"pr-{number}"
            shutil.move(str(candidate), str(destination))
        if candidate.exists():
            shutil.rmtree(candidate)
        print(f"Restored {name} from workflow run {run_id}")
        return True
    print(f"Missing passing artifact for {name}; not publishing a stale snapshot")
    return False


def main() -> None:
    """Collect passing source-verified snapshots for one Pages publication."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--staging", required=True, type=Path)
    args = parser.parse_args()
    if not args.repo or not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        parser.error("A GitHub owner/repository is required")
    if args.staging.exists():
        raise FileExistsError(f"Refusing nonempty staging directory: {args.staging}")
    args.staging.mkdir(parents=True)
    restore(
        args.repo,
        args.staging,
        "docs-main",
        "Build Main Documentation",
        {"push", "workflow_dispatch"},
        "main",
    )
    for number, head in sorted(open_same_repo_prs(args.repo).items()):
        restore(
            args.repo,
            args.staging,
            f"docs-preview-{number}",
            "Preview Documentation",
            {"pull_request"},
            head["branch"],
            head["sha"],
        )


if __name__ == "__main__":
    main()
