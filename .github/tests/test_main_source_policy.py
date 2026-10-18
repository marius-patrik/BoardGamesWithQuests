"""Validate the release-branch source restriction from the native trusted workflow."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class MainSourcePolicyTests(unittest.TestCase):
    def test_main_gate_checks_only_the_development_head(self) -> None:
        workflow = (ROOT / ".github/workflows/main-source.yml").read_text(encoding="utf-8")
        self.assertIn("  pull_request_target:", workflow)
        self.assertIn("    branches: [main]", workflow)
        self.assertIn("    name: main-source", workflow)
        self.assertIn("SOURCE_REPO: ${{ github.event.pull_request.head.repo.full_name }}", workflow)
        self.assertIn("SOURCE_BRANCH: ${{ github.event.pull_request.head.ref }}", workflow)
        self.assertIn("TARGET_BRANCH: ${{ github.event.pull_request.base.ref }}", workflow)
        self.assertIn('[ "$SOURCE_REPO" != "$GITHUB_REPOSITORY" ]', workflow)
        self.assertIn('[ "$SOURCE_BRANCH" != "development" ]', workflow)
        self.assertIn('[ "$TARGET_BRANCH" != "main" ]', workflow)
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
