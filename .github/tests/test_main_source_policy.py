"""Validate the release-branch source restriction from the native trusted workflow."""

from __future__ import annotations

import unittest
import os
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class MainSourcePolicyTests(unittest.TestCase):
    def test_main_gate_checks_develop_and_pinned_upstream_sync(self) -> None:
        workflow = (ROOT / ".github/workflows/main-source.yml").read_text(encoding="utf-8")
        self.assertIn("  pull_request_target:", workflow)
        self.assertIn("    branches: [main]", workflow)
        self.assertIn("    name: main-source", workflow)
        self.assertIn("SOURCE_REPO: ${{ github.event.pull_request.head.repo.full_name }}", workflow)
        self.assertIn("SOURCE_BRANCH: ${{ github.event.pull_request.head.ref }}", workflow)
        self.assertIn("TARGET_BRANCH: ${{ github.event.pull_request.base.ref }}", workflow)
        self.assertIn('[ "$SOURCE_REPO" != "$GITHUB_REPOSITORY" ]', workflow)
        self.assertIn('[ "$SOURCE_BRANCH" != "develop" ]', workflow)
        self.assertIn('[ "$TARGET_BRANCH" != "main" ]', workflow)
        self.assertNotIn("actions/checkout", workflow)

    def test_trusted_shell_restricts_release_and_unpinned_branches(self) -> None:
        workflow = (ROOT / ".github/workflows/main-source.yml").read_text(encoding="utf-8")
        script = textwrap.dedent(workflow.split("run: |", 1)[1])
        repo = "marius-patrik/BoardGamesWithQuests"
        for source_repo, source_branch, target, accepted in (
            (repo, "develop", "main", True),
            (repo, "feature/other", "main", False),
            (repo, "chore/479-sync-upstream-main", "main", False),  # missing pinned provenance
            ("attacker/BoardGamesWithQuests", "develop", "main", False),
            (repo, "develop", "develop", False),
            (repo, "develop; exit 0", "main", False),
        ):
            with self.subTest(source_repo=source_repo, branch=source_branch, target=target):
                result = subprocess.run(
                    ["bash", "-c", script],
                    text=True,
                    capture_output=True,
                    env=dict(
                        os.environ,
                        GITHUB_REPOSITORY=repo,
                        SOURCE_REPO=source_repo,
                        SOURCE_BRANCH=source_branch,
                        TARGET_BRANCH=target,
                    ),
                )
                self.assertEqual(result.returncode == 0, accepted, result.stderr)

    def test_upstream_exception_pins_exact_source_and_delta(self) -> None:
        workflow = (ROOT / ".github/workflows/main-source.yml").read_text(encoding="utf-8")
        self.assertIn('"chore/479-sync-upstream-main"', workflow)
        self.assertIn('3bc11ca3621ca5d497aff3bab071ac6d222dadcc', workflow)
        self.assertIn('a98e36d098a1ee9aa3e793cfc39040ad6e6d2e4e', workflow)
        self.assertIn('repos/docekalgjkt/ChessWithQuests/branches/main', workflow)
        self.assertIn('.ahead_by == 1 and .behind_by == 0', workflow)
        self.assertIn('.files[0].filename == "model/figurka.py"', workflow)
        self.assertNotIn("actions/checkout", workflow)

    def test_main_protection_requires_the_source_check(self) -> None:
        import json

        config = json.loads((ROOT / "repo.dfconfig").read_text(encoding="utf-8"))
        lanes = config["repo"]["protection"]["lanes"]
        main = next(lane for lane in lanes if lane["branch"] == "main")
        self.assertIn("main-source", main["required_checks"])
        self.assertTrue(main["enforce_admins"])
        self.assertGreaterEqual(main["approvals"], 1)


if __name__ == "__main__":
    unittest.main()
