"""Generate the published documentation site's selectors from deployable files.

The project registry has exactly one source: repo.documentation.projects
in the checked-out repository's repo.dfconfig. Versions are listed only
when their index.html exists inside the deployment artifact.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


def project_registry(repository: Path) -> list[dict[str, str]]:
    """Return and validate the documentation projects declared in repo.dfconfig."""
    config = json.loads((repository / "repo.dfconfig").read_text(encoding="utf-8"))
    repo = config.get("repo", {})
    if not isinstance(repo, dict):
        raise ValueError("repo.dfconfig requires a 'repo' object")
    docs = repo.get("documentation") or {}
    if not isinstance(docs, dict):
        raise ValueError("repo.documentation must be an object")
    declared = docs.get("projects", [])
    if not isinstance(declared, list):
        raise ValueError("repo.documentation.projects must be a list")

    projects: list[dict[str, str]] = []
    names: set[str] = set()
    urls: set[str] = set()
    for index, entry in enumerate(declared):
        if not isinstance(entry, dict):
            raise ValueError(f"Project {index} must be an object")
        name, url = entry.get("name"), entry.get("url")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Project {index} requires a nonempty name")
        if not isinstance(url, str):
            raise ValueError(f"Project {index} requires an HTTPS URL")
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(f"Project {index} requires an absolute public HTTPS URL")
        canonical_name = name.strip()
        canonical_url = url.rstrip("/") + "/"
        if canonical_name in names or canonical_url in urls:
            raise ValueError(f"Duplicate documentation project: {canonical_name}")
        names.add(canonical_name)
        urls.add(canonical_url)
        projects.append({"name": canonical_name, "url": canonical_url})
    return projects


def manifest(site: Path, repository: Path) -> dict[str, list[dict[str, str]]]:
    """Describe only sites whose root HTML is present in the deployment artifact."""
    if not (site / "index.html").is_file():
        raise ValueError(f"Documentation site is missing {site / 'index.html'}")

    config = json.loads((repository / "repo.dfconfig").read_text(encoding="utf-8"))
    identity = config.get("repo", {}).get("identity", {})
    default_branch = identity.get("default_branch") if isinstance(identity, dict) else None
    if not isinstance(default_branch, str) or not default_branch:
        default_branch = "repository root"
    versions = [{"name": default_branch, "path": ""}]
    branches = site / "branch"
    if branches.is_dir():
        for path in sorted(branches.iterdir()):
            if path.is_dir() and (path / "index.html").is_file():
                versions.append({"name": path.name, "path": f"branch/{path.name}"})
    previews = sorted(
        (
            path
            for path in site.iterdir()
            if path.is_dir()
            and path.name.startswith("pr-")
            and path.name[3:].isdigit()
            and (path / "index.html").is_file()
        ),
        key=lambda path: int(path.name[3:]),
        reverse=True,
    )
    for path in previews:
        versions.append({"name": f"PR #{path.name[3:]}", "path": path.name})
    return {"versions": versions, "projects": project_registry(repository)}


def main() -> None:
    """Write a deterministic manifest from actual deployable site contents."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=Path("site"))
    args = parser.parse_args()
    site = args.site.resolve()
    data = manifest(site, Path(__file__).resolve().parents[2])
    (site / "versions.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
