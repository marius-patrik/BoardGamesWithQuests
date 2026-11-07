#!/usr/bin/env python3
"""Reconcile noncritical PR deployment metadata after a successful Pages publication."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import quote


class APIError(RuntimeError):
    """An actual GitHub API HTTP error, retaining its status and response."""

    def __init__(self, status: int, response: str) -> None:
        self.status = status
        self.response = response
        super().__init__(f"GitHub API HTTP {status}: {response}")


class GitHubAPI:
    """Small authenticated GitHub REST client for deployment metadata only."""

    def __init__(self, repo: str, token: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("Invalid repository identity")
        if not token:
            raise ValueError("GH_TOKEN is required")
        self.base = f"https://api.github.com/repos/{repo}/"
        self.token = token

    def request(self, method: str, endpoint: str, payload: dict | None = None) -> object:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            self.base + endpoint,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "BoardGamesWithQuests-docs-publisher",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise APIError(error.code, body) from error

    def get(self, endpoint: str) -> object:
        return self.request("GET", endpoint)

    def post(self, endpoint: str, payload: dict) -> object:
        return self.request("POST", endpoint, payload)


def records(api: GitHubAPI, path: str) -> list[dict]:
    """Read all pages; failure to read any page is fatal, never treated as empty."""
    entries: list[dict] = []
    for page in range(1, 101):
        result = api.get(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
        if not isinstance(result, list) or any(not isinstance(item, dict) for item in result):
            raise ValueError("Invalid GitHub deployment-list response")
        entries.extend(result)
        if len(result) < 100:
            return entries
    raise ValueError("GitHub deployment pagination limit exceeded")


def preview_post(
    api: GitHubAPI, pr: str, operation: str, endpoint: str, data: dict
) -> object | None:
    """Only HTTP 422 on noncritical PR metadata writes is a warning."""
    try:
        return api.post(endpoint, data)
    except APIError as error:
        if error.status != 422:
            raise
        response = (
            error.response[:2000].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        )
        print(
            f"::warning title=Preview deployment metadata HTTP 422::"
            f"PR #{pr}: {operation} rejected with HTTP 422; API response: {response}",
            flush=True,
        )
        return None


def reconcile(api: GitHubAPI, previews: dict[str, str], page_url: str) -> None:
    """Update metadata after Pages succeeds, without hiding unexpected API errors."""
    if not page_url.startswith("https://"):
        raise ValueError("Expected an HTTPS GitHub Pages deployment URL")
    if not isinstance(previews, dict):
        raise ValueError("Preview index must be a JSON object")
    for pr, sha in previews.items():
        if (
            not re.fullmatch(r"[1-9][0-9]*", pr)
            or not isinstance(sha, str)
            or not re.fullmatch(r"[0-9a-f]{40}", sha)
        ):
            raise ValueError("Invalid preview PR number or source SHA")

    for pr, sha in sorted(previews.items(), key=lambda entry: int(entry[0])):
        head = api.get(f"pulls/{pr}")
        if not isinstance(head, dict) or not isinstance(head.get("head"), dict):
            raise ValueError(f"Invalid PR #{pr} response")
        if head["head"].get("sha") != sha:
            continue
        existing = records(api, f"deployments?environment=pr-{quote(pr)}")
        matches = [row for row in existing if row.get("sha") == sha]
        if matches:
            deployment = matches[0].get("id")
        else:
            created = preview_post(
                api,
                pr,
                "deployment creation",
                "deployments",
                {
                    "ref": sha,
                    "environment": f"pr-{pr}",
                    "auto_merge": False,
                    "transient_environment": True,
                    "required_contexts": [],
                    "description": "Documentation preview",
                },
            )
            if created is None:
                continue
            if not isinstance(created, dict):
                raise ValueError(f"Invalid PR #{pr} deployment creation response")
            deployment = created.get("id")
        if not isinstance(deployment, int) or deployment <= 0:
            raise ValueError(f"Invalid PR #{pr} deployment ID")
        preview_post(
            api,
            pr,
            "success-status update",
            f"deployments/{deployment}/statuses",
            {
                "state": "success",
                "environment_url": f"{page_url.rstrip('/')}/pr-{pr}/",
                "description": "Published via GitHub Pages Actions",
            },
        )

    for row in records(api, "deployments"):
        environment = row.get("environment")
        if not isinstance(environment, str):
            continue
        match = re.fullmatch(r"pr-([1-9][0-9]*)", environment)
        if match is None:
            continue
        pr = match.group(1)
        if row.get("sha") == previews.get(pr):
            continue
        deployment = row.get("id")
        if not isinstance(deployment, int) or deployment <= 0:
            raise ValueError(f"Invalid obsolete PR #{pr} deployment ID")
        status = api.get(f"deployments/{deployment}/statuses?per_page=1")
        if not isinstance(status, list) or any(not isinstance(item, dict) for item in status):
            raise ValueError(f"Invalid PR #{pr} deployment status response")
        if status and status[0].get("state") == "inactive":
            continue
        preview_post(
            api,
            pr,
            "stale-deployment retirement",
            f"deployments/{deployment}/statuses",
            {"state": "inactive", "description": "Preview not in published Pages site"},
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--previews", required=True)
    parser.add_argument("--page-url", required=True)
    args = parser.parse_args()
    reconcile(
        GitHubAPI(args.repo, os.environ.get("GH_TOKEN", "")),
        json.loads(args.previews),
        args.page_url,
    )


if __name__ == "__main__":
    main()
