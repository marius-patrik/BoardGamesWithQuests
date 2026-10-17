"""Assemble independent PR documentation builds for one GitHub Pages publication.

The GitHub Pages Actions API publishes one complete artifact per repository.
The assembler reuses the latest successfully staged production site, accepts
already-built PR artifacts without rebuilding main, and drops closed previews.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


def assemble(staging: Path, site: Path, open_prs: set[int]) -> list[int]:
    """Publish a coherent site from staged artifacts without running any builder."""
    if not staging.is_dir():
        raise FileNotFoundError(f"Documentation staging directory is missing: {staging}")
    if any(path.is_symlink() for path in staging.rglob("*")):
        raise ValueError("Refusing symlinks in staged Pages artifacts")
    if site.exists():
        shutil.rmtree(site)
    shutil.copytree(staging, site, symlinks=False)

    published: list[int] = []
    for child in site.iterdir():
        if not child.is_dir() or not re.fullmatch(r"pr-\d+", child.name):
            continue
        number = int(child.name[3:])
        if number not in open_prs or not (child / "index.html").is_file():
            shutil.rmtree(child)
            continue
        published.append(number)

    published.sort(reverse=True)
    if not (site / "index.html").is_file():
        # A missing/failed main build must not make PR sites impossible to deploy.
        # Present an honest index until a successful main build is staged.
        links = "\n".join(
            f'<li><a href="pr-{number}/">PR #{number}</a></li>' for number in published
        )
        landing = (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            "<title>Documentation previews</title></head><body>"
            "<h1>Documentation previews</h1><p>The production documentation "
            "build is unavailable. Published pull-request builds are independent "
            "of that build.</p><ul>" + links + "</ul></body></html>"
        )
        (site / "index.html").write_text(landing, encoding="utf-8")
    (site / ".nojekyll").touch()
    return published


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--open-prs", nargs="*", type=int, default=[])
    args = parser.parse_args()
    published = assemble(args.staging, args.site, set(args.open_prs))
    print(f"Pages artifact includes {len(published)} open PR previews: {published}")


if __name__ == "__main__":
    main()
