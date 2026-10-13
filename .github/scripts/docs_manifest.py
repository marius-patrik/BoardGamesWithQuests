"""Emit the Pages selector manifest from builds included in the deployment.

Only URLs of actual deployed HTML roots are advertised. Preview discovery is based
on directories copied into the Actions artifact, not on stale gh-pages manifests.
"""

import argparse
import json
from pathlib import Path


def manifest(site: Path, repository: Path) -> dict:
    """Return the current repository, available builds and known sister sites."""
    versions = [{"name": "main", "path": ""}]
    branches = site / "branch"
    if branches.is_dir():
        for path in sorted(branches.iterdir()):
            if path.is_dir() and (path / "index.html").exists():
                versions.append({"name": path.name, "path": f"branch/{path.name}"})
    previews = sorted(
        (path for path in site.glob("pr-*") if path.is_dir() and (path / "index.html").exists()),
        key=lambda path: int(path.name[3:]) if path.name[3:].isdigit() else -1,
        reverse=True,
    )
    for path in previews:
        if path.name[3:].isdigit():
            versions.append({"name": f"PR #{path.name[3:]}", "path": path.name})
    settings = json.loads((repository / "repo.dfconfig").read_text(encoding="utf-8")).get("repo", {})
    projects = [
        {"name": entry["name"], "url": entry["url"]}
        for entry in settings.get("documentation", {}).get("projects", [])
        if isinstance(entry, dict) and entry.get("name") and entry.get("url")
    ]
    return {"versions": versions, "projects": projects}


def main() -> None:
    """Write the selector manifest into the site that will actually be uploaded."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=Path("site"))
    args = parser.parse_args()
    site = args.site.resolve()
    content = manifest(site, Path(__file__).resolve().parents[2])
    (site / "versions.json").write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
