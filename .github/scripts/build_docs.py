"""Build documentation from the repository root using a temporary virtual docs source.

MkDocs rejects a docs_dir containing the configuration itself. Instead of
committing a fake docs directory, build an ephemeral config and empty docs_dir in
the OS temporary directory. The hook reads tracked content from the actual repo root.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def ensure_graphviz() -> None:
    """Install the renderer on Linux CI runners if the base image omitted it.

    Local development intentionally requires the system Graphviz package:
    documentation must show real UML edges, not silently fall back to a list.
    """
    if shutil.which("dot"):
        return
    if os.environ.get("CI", "").lower() != "true" or sys.platform != "linux":
        raise RuntimeError(
            "Graphviz 'dot' is required for generated UML. Install graphviz locally."
        )
    installer = [] if os.geteuid() == 0 else ["sudo"]
    subprocess.run([*installer, "apt-get", "update", "-qq"], check=True)
    subprocess.run([*installer, "apt-get", "install", "-y", "-qq", "graphviz"], check=True)
    if not shutil.which("dot"):
        raise RuntimeError("Graphviz did not become available after installation.")


def build(root: Path = ROOT, site: Path | None = None) -> None:
    """Render the site without creating a documentation source directory in Git."""
    ensure_graphviz()
    with tempfile.TemporaryDirectory(prefix="repo-docs-") as temporary:
        work = Path(temporary)
        source = work / "source"
        source.mkdir()
        config = yaml.safe_load((root / "mkdocs.yml").read_text(encoding="utf-8"))
        config["docs_dir"] = str(source)
        config["site_dir"] = str(site or root / "site")
        config["hooks"] = [str((root / hook).resolve()) for hook in config.get("hooks", [])]
        theme = config.get("theme", {})
        if theme.get("custom_dir"):
            theme["custom_dir"] = str((root / theme["custom_dir"]).resolve())

        # Discover import roots from project metadata, not a hardcoded package list.
        sys.path.insert(0, str((ROOT / ".github" / "scripts").resolve()))
        from docs_hooks import python_roots

        for plugin in config.get("plugins", []):
            if isinstance(plugin, dict) and "mkdocstrings" in plugin:
                handlers = plugin["mkdocstrings"].setdefault("handlers", {})
                python = handlers.setdefault("python", {})
                python["paths"] = [str(path) for path in python_roots(root)]
        ephemeral = work / "mkdocs.yml"
        ephemeral.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "--strict", "-f", str(ephemeral)],
            cwd=root,
            check=True,
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--site", type=Path)
    args = parser.parse_args()
    build(args.repo.resolve(), args.site.resolve() if args.site else None)
