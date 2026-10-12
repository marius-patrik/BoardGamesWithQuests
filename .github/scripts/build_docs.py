"""Build documentation from the repository root using a temporary virtual docs source.

ProperDocs/MkDocs reject a docs_dir containing the configuration itself. Instead of
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


def build() -> None:
    """Render the site without creating a documentation source directory in Git."""
    ensure_graphviz()
    with tempfile.TemporaryDirectory(prefix="repo-docs-") as temporary:
        work = Path(temporary)
        source = work / "source"
        source.mkdir()
        config = yaml.safe_load((ROOT / "properdocs.yml").read_text(encoding="utf-8"))
        config["docs_dir"] = str(source)
        config["site_dir"] = str(ROOT / "site")
        config["hooks"] = [str((ROOT / hook).resolve()) for hook in config.get("hooks", [])]
        theme = config.get("theme", {})
        if theme.get("custom_dir"):
            theme["custom_dir"] = str((ROOT / theme["custom_dir"]).resolve())

        # Discover import roots from project metadata, not a hardcoded package list.
        sys.path.insert(0, str((ROOT / ".github" / "scripts").resolve()))
        from docs_hooks import python_roots

        for plugin in config.get("plugins", []):
            if isinstance(plugin, dict) and "mkdocstrings" in plugin:
                handlers = plugin["mkdocstrings"].setdefault("handlers", {})
                python = handlers.setdefault("python", {})
                python["paths"] = [str(path) for path in python_roots()]
        ephemeral = work / "properdocs.yml"
        ephemeral.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "properdocs", "build", "--strict", "-f", str(ephemeral)],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    build()
