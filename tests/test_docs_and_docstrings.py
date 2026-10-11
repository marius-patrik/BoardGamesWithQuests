"""Behavioral tests for repository-root documentation generation."""

import ast
import importlib.util
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest
from properdocs.structure.files import Files

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".github" / "scripts" / "docs_hooks.py"
spec = importlib.util.spec_from_file_location("repo_docs_hook", HOOK)
docs = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = docs
spec.loader.exec_module(docs)


def targets(nav):
    """Collect leaf targets from an arbitrarily nested navigation."""
    if isinstance(nav, str):
        return [nav]
    if isinstance(nav, list):
        return [target for item in nav for target in targets(item)]
    return [target for child in nav.values() for target in targets(child)]


def fixture_repo(tmp_path):
    """Create a tracked mini repository that contains no documentation configuration."""
    root = tmp_path / "example"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "src" / "example").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "notes").mkdir()
    (root / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\npythonpath = ["src", "."]\n', encoding="utf-8"
    )
    (root / "README.md").write_text("# Example\n", encoding="utf-8")
    (root / "notes" / "guide.md").write_text("# A guide\n", encoding="utf-8")
    (root / "src" / "example" / "__init__.py").write_text(
        '"""An example package."""\n', encoding="utf-8"
    )
    (root / "src" / "example" / "unit.py").write_text('"""An example unit."""\n', encoding="utf-8")
    (root / "tests" / "test_unit.py").write_text('"""A test module."""\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    return root


def test_repository_files_are_discovered_without_a_source_path_list():
    """Python modules and Markdown anywhere in a tracked repository are included."""
    nav, pages = docs.build_nav(ROOT)
    by_path = dict(pages)
    assert "index.md" in by_path
    assert "model/game/board.md" in by_path
    assert "tests/test_docs_and_docstrings.md" in by_path
    assert "AGENTS.md" in by_path
    assert "notes/object_model.md" in by_path
    assert set(targets(nav)) == set(by_path)


def test_new_and_renamed_content_automatically_updates_pages_and_navigation(tmp_path):
    """Discovery follows Git's index rather than a hardcoded tree or section list."""
    root = fixture_repo(tmp_path)
    original_nav, original_pages = docs.build_nav(root)
    before = dict(original_pages)
    assert before["index.md"] == "# Example\n"
    assert before["notes/guide.md"] == "# A guide\n"
    assert "example/unit.md" in before
    assert "tests/test_unit.md" in before
    assert set(targets(original_nav)) == set(before)

    old = root / "src" / "example" / "unit.py"
    renamed = old.with_name("renamed.py")
    old.rename(renamed)
    (root / "independent.md").write_text("# Independent\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    updated_nav, updated_pages = docs.build_nav(root)
    after = dict(updated_pages)
    assert "example/unit.md" not in after
    assert "example/renamed.md" in after
    assert after["independent.md"] == "# Independent\n"
    assert set(targets(updated_nav)) == set(after)


def test_import_paths_and_directory_labels_are_derived_from_metadata(tmp_path):
    """Arbitrarily named packages yield importable API directives and package hubs."""
    root = fixture_repo(tmp_path)
    nav, pages = docs.build_nav(root)
    by_path = dict(pages)
    assert "::: example" in by_path["example/index.md"]
    assert "::: example.unit" in by_path["example/unit.md"]
    assert "Source_Roots" not in str(nav)
    assert "example" in str(nav).lower()


def test_untracked_build_outputs_and_ignored_content_do_not_leak_into_docs(tmp_path):
    """Only Git-tracked source is eligible, not arbitrary files in a checkout."""
    root = fixture_repo(tmp_path)
    (root / "notes" / "draft.md").write_text("# Untracked\n", encoding="utf-8")
    (root / "site").mkdir()
    (root / "site" / "index.md").write_text("# Old output\n", encoding="utf-8")
    pages = dict(docs.build_nav(root)[1])
    assert "notes/draft.md" not in pages
    assert "site/index.md" not in pages


def test_every_tracked_importable_module_has_google_docstrings():
    """Preserve the original source module docstring coverage across discovered packages."""
    missing = []
    roots = docs.python_roots(ROOT)
    source_roots = [root for root in roots if root != ROOT]
    for path in docs.tracked_files(ROOT):
        if path.suffix != ".py" or docs.import_name(path, roots) is None:
            continue
        # Test packages are discoverable documentation, but the production API
        # docstring gate applies only to source roots declared by the project.
        if source_roots and not any(path.is_relative_to(root) for root in source_roots):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if not ast.get_docstring(tree):
            missing.append(f"{path}: module")
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and not ast.get_docstring(node):
                if not node.name.startswith("_") or isinstance(node, ast.ClassDef):
                    missing.append(f"{path}: {node.name}")
    assert not missing, "Missing docstrings: " + ", ".join(missing)


def test_virtual_files_use_the_same_source_as_navigation(tmp_path):
    """No documentation source page is written to or stored in the repository."""
    config = SimpleNamespace(
        plugins=SimpleNamespace(_current_plugin=None),
        docs_dir=str(tmp_path),
        site_dir=str(tmp_path / "site"),
        use_directory_urls=True,
    )
    files = docs.on_files(Files([]), config)
    paths = {file.src_uri for file in files}
    assert paths == set(dict(docs.build_nav(ROOT)[1]))
    assert docs.on_files(files, config) is files


def test_no_placeholder_docs_directory_is_tracked():
    """The documentation system does not rely on a .docs directory."""
    assert not (ROOT / ".docs").exists()
    assert not any(".docs" in p.parts for p in docs.tracked_files(ROOT))


def test_strict_documentation_build():
    """Documentation must render successfully from the actual repository root."""
    result = subprocess.run(
        [sys.executable, ".github/scripts/build_docs.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert (ROOT / "site" / "index.html").is_file()
    assert (ROOT / "site" / "model" / "game" / "board" / "index.html").is_file()
