#!/usr/bin/env python3
"""Fail closed before a release from the verified main branch publishes immutable tags."""

from __future__ import annotations

import argparse
import re
import sys

SHA = re.compile(r"^[0-9a-f]{40}$")


def authorize_release(
    event: str,
    ref: str,
    repository: str,
    run_sha: str,
    live_main_sha: str,
    checkout_sha: str,
) -> None:
    if event not in {"workflow_dispatch", "push"}:
        raise ValueError("A release must be triggered by a main push or an explicit main dispatch")
    if ref != "refs/heads/main" or repository != "marius-patrik/BoardGamesWithQuests":
        raise ValueError(
            "Only a release event targeting the project main branch can publish"
        )
    if any(not SHA.fullmatch(sha) for sha in (run_sha, live_main_sha, checkout_sha)):
        raise ValueError("Missing or invalid commit SHA")
    if run_sha != live_main_sha or checkout_sha != live_main_sha:
        raise ValueError("The release candidate is not the live main HEAD")


def validate_existing_tag(tag: str, candidate_sha: str, assigned_sha: str | None) -> None:
    if not tag or tag.startswith("-") or any(char.isspace() for char in tag):
        raise ValueError("Invalid or missing release tag")
    if not SHA.fullmatch(candidate_sha):
        raise ValueError("Missing or invalid candidate commit SHA")
    if assigned_sha is not None and (
        not SHA.fullmatch(assigned_sha) or assigned_sha != candidate_sha
    ):
        raise ValueError(f"Tag {tag} is assigned to a different commit")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    release = commands.add_parser("release")
    for name in ("event", "ref", "repository", "run-sha", "live-sha", "checkout-sha"):
        release.add_argument(f"--{name}", required=True)
    tag = commands.add_parser("tag")
    tag.add_argument("--tag", required=True)
    tag.add_argument("--run-sha", required=True)
    tag.add_argument("--assigned-sha")
    args = parser.parse_args()
    try:
        if args.action == "release":
            authorize_release(
                args.event,
                args.ref,
                args.repository,
                args.run_sha,
                args.live_sha,
                args.checkout_sha,
            )
        else:
            validate_existing_tag(args.tag, args.run_sha, args.assigned_sha)
    except ValueError as error:
        print(f"release gate: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
