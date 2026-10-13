"""One-time, evidence-based GitHub Project #14 status reconciliation.

Uses GitHub GraphQL API via a project-scoped token; never alters GitHub issue
states, closes pull requests, or invents completed implementation.
"""

from __future__ import annotations

import json
import os
import time
from urllib.request import Request, urlopen

TOKEN = os.environ["GH_TOKEN"]
OWNER = "marius-patrik"
PROJECT = 14
URL = "https://api.github.com/graphql"


def query(document: str, **variables: object) -> dict:
    """Execute one authenticated GraphQL operation or reject partial results."""
    data = json.dumps({"query": document, "variables": variables}).encode()
    request = Request(
        URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "BoardGamesWithQuests-G0",
        },
    )
    with urlopen(request, timeout=45) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(f"GitHub GraphQL failed: {result['errors']}")
    return result["data"]


METADATA = """
query($owner: String!, $number: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      id
      fields(first: 100) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id
            name
            options { id name }
          }
        }
      }
    }
  }
}
"""

ITEMS = """
query($owner: String!, $number: Int!, $after: String) {
  user(login: $owner) {
    projectV2(number: $number) {
      items(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            __typename
            ... on Issue {
              number title state stateReason url
              labels(first: 50) { nodes { name } }
            }
            ... on PullRequest {
              number title state merged url
              labels(first: 50) { nodes { name } }
            }
          }
          fieldValues(first: 30) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field {
                  ... on ProjectV2SingleSelectField { name }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

UPDATE = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $project
      itemId: $item
      fieldId: $field
      value: { singleSelectOptionId: $option }
    }
  ) { projectV2Item { id } }
}
"""


def desired(item: dict) -> str | None:
    """Classify from real closure and labels, never from an old board status."""
    content = item.get("content")
    if not content:
        return None
    labels = {node["name"] for node in content.get("labels", {}).get("nodes", [])}
    kind = content.get("__typename")
    state = content.get("state")
    title = content.get("title", "").lower()

    if kind == "PullRequest":
        if state == "MERGED" or content.get("merged"):
            return "Done"
        if state == "OPEN":
            return "In Progress"
        if "Dropped" in labels or title.startswith("[not planned]"):
            return "Dropped"
        if "Superseded" in labels or title.startswith("[superseded"):
            return "Superseded"
        return "Dropped"

    if kind == "Issue":
        if state == "OPEN":
            if "In Progress" in labels:
                return "In Progress"
            return "ToDo"
        if "Superseded" in labels:
            return "Superseded"
        if "Dropped" in labels:
            return "Dropped"
        if content.get("stateReason") == "NOT_PLANNED":
            return "Superseded" if "Plan" in labels else "Dropped"
        return "Done"

    return None


def main() -> None:
    """Apply deterministic project status corrections and verify every write."""
    data = query(METADATA, owner=OWNER, number=PROJECT)["user"]["projectV2"]
    project_id = data["id"]
    status = next(field for field in data["fields"]["nodes"] if field and field["name"] == "Status")
    options = {option["name"]: option["id"] for option in status["options"]}
    changes = []
    count = 0
    cursor = None
    while True:
        result = query(ITEMS, owner=OWNER, number=PROJECT, after=cursor)
        items = result["user"]["projectV2"]["items"]
        for item in items["nodes"]:
            count += 1
            target = desired(item)
            if target is None:
                continue
            current = next(
                (
                    value.get("name")
                    for value in item["fieldValues"]["nodes"]
                    if value and value.get("field", {}).get("name") == "Status"
                ),
                None,
            )
            if current != target:
                content = item["content"]
                changes.append((item["id"], content["url"], current, target))
        if not items["pageInfo"]["hasNextPage"]:
            break
        cursor = items["pageInfo"]["endCursor"]

    print(f"Audited {count} project items; reconciling {len(changes)} statuses.")
    for item_id, url, before, target in changes:
        print(f"{url}: {before or '(unset)'} -> {target}")
        query(
            UPDATE,
            project=project_id,
            item=item_id,
            field=status["id"],
            option=options[target],
        )
        time.sleep(0.2)

    # Re-read item statuses rather than equating successful mutations with truth.
    cursor = None
    remaining = []
    while True:
        response = query(ITEMS, owner=OWNER, number=PROJECT, after=cursor)
        batch = response["user"]["projectV2"]["items"]
        for item in batch["nodes"]:
            target = desired(item)
            if target is None:
                continue
            actual = next(
                (
                    value.get("name")
                    for value in item["fieldValues"]["nodes"]
                    if value and value.get("field", {}).get("name") == "Status"
                ),
                None,
            )
            if target != actual:
                remaining.append((item["content"]["url"], actual, target))
        if not batch["pageInfo"]["hasNextPage"]:
            break
        cursor = batch["pageInfo"]["endCursor"]

    if remaining:
        raise RuntimeError(f"Project status verification failed: {remaining}")
    print("Project #14 status reconciliation verified without changing issue states.")


if __name__ == "__main__":
    main()
