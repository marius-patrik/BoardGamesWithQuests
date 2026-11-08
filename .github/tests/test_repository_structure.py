"""Repository contracts for the cleanroom product and documentation layout."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))
import validate_repository
import generate_diagrams


class CleanroomLayoutTests(unittest.TestCase):
    def test_only_canonical_documents_and_symlinks(self) -> None:
        self.assertEqual(validate_repository.validate_layout(), [])
        for link, target in (
            ("README.md", ".agents/PRD.md"),
            ("CONTRIBUTING.md", ".agents/AGENTS.md"),
        ):
            actual = ROOT / link
            if actual.is_symlink():
                self.assertEqual(actual.readlink().as_posix(), target)
            elif sys.platform == "win32":
                self.assertEqual(actual.read_text(encoding="utf-8").strip(), target)
            else:
                self.fail(f"Expected a real symlink: {link}")

    def test_obsolete_package_and_agent_artifacts_are_absent(self) -> None:
        for path in (
            *validate_repository.OBSOLETE_DIRECTORIES,
            *validate_repository.OBSOLETE_DOCUMENTS,
        ):
            with self.subTest(path=path):
                self.assertFalse((ROOT / path).exists())
        for name in ("model", "view", "controller"):
            self.assertTrue((ROOT / "src" / name / "__init__.py").is_file())
            self.assertFalse((ROOT / name).exists())

    def test_mermaid_owners_and_python_uml_sources(self) -> None:
        # UML itself needs only the standard library. Avoid parsing the full
        # tracked repository AST in a small layout test.
        with patch.object(
            generate_diagrams, "repository_ast", return_value="flowchart LR\\n"
        ):
            names = set(generate_diagrams.generated_assets(ROOT))
        self.assertEqual(
            names,
            {
                "docs/architecture/diagrams/ast.mmd",
                "docs/architecture/diagrams/uml.mmd",
            },
        )
        uml = generate_diagrams.implementation_uml(ROOT)
        self.assertIn('["GameManagerController"]', uml)
        self.assertIn('["GameManager"]', uml)
        self.assertNotIn('["GameController"]', uml)
        for ignored in ("CleanroomLayoutTests", "ReleaseGateBehaviorTests"):
            self.assertNotIn(f'["{ignored}"]', uml)

    def test_validation_cli(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / ".github/scripts/validate_repository.py"),
                "--check",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_external_tests(self) -> None:
        fake = subprocess.CompletedProcess(
            args=["git", "ls-files", "-z", "--cached"],
            returncode=0,
            stdout=b"unrelated/tests/test_bad.py\0",
            stderr=b"",
        )
        with patch.object(validate_repository.subprocess, "run", return_value=fake):
            errors = validate_repository.validate_layout()
        self.assertTrue(any("unrelated/tests/test_bad.py" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
