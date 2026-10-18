"""Behavioral tests for fail-closed release authorization using the real CLI boundary."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/release_gate.py"
SHA1 = "a" * 40
SHA2 = "b" * 40


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def dispatch(
    *,
    event: str = "workflow_dispatch",
    ref: str = "refs/heads/main",
    repository: str = "marius-patrik/BoardGamesWithQuests",
    run_sha: str = SHA1,
    live_sha: str = SHA1,
    checkout_sha: str = SHA1,
) -> subprocess.CompletedProcess[str]:
    return invoke(
        "release",
        "--event",
        event,
        "--ref",
        ref,
        "--repository",
        repository,
        "--run-sha",
        run_sha,
        "--live-sha",
        live_sha,
        "--checkout-sha",
        checkout_sha,
    )


class ReleaseGateBehaviorTests(unittest.TestCase):
    def test_valid_main_push_and_explicit_dispatch_succeed(self) -> None:
        self.assertEqual(dispatch(event="push").returncode, 0)
        self.assertEqual(dispatch(event="workflow_dispatch").returncode, 0)

    def test_pull_request_and_schedule_cannot_release(self) -> None:
        for event in ("pull_request", "schedule"):
            with self.subTest(event=event):
                self.assertNotEqual(dispatch(event=event).returncode, 0)

    def test_other_ref_or_repository_cannot_release(self) -> None:
        self.assertNotEqual(dispatch(ref="refs/heads/develop").returncode, 0)
        self.assertNotEqual(dispatch(ref="refs/tags/v1.0.0").returncode, 0)
        self.assertNotEqual(dispatch(repository="another/project").returncode, 0)

    def test_stale_or_unrelated_head_is_rejected(self) -> None:
        self.assertNotEqual(dispatch(live_sha=SHA2).returncode, 0)
        self.assertNotEqual(dispatch(checkout_sha=SHA2).returncode, 0)

    def test_invalid_commit_sha_is_rejected(self) -> None:
        self.assertNotEqual(dispatch(run_sha="short").returncode, 0)

    def test_unused_and_matching_tags_are_accepted(self) -> None:
        self.assertEqual(invoke("tag", "--tag", "v1.2.3", "--run-sha", SHA1).returncode, 0)
        self.assertEqual(
            invoke("tag", "--tag", "v1.2.3", "--run-sha", SHA1, "--assigned-sha", SHA1).returncode,
            0,
        )

    def test_existing_different_tag_commit_is_never_reused(self) -> None:
        self.assertNotEqual(
            invoke("tag", "--tag", "v1.2.3", "--run-sha", SHA1, "--assigned-sha", SHA2).returncode,
            0,
        )

    def test_invalid_tag_or_ambiguous_assignment_is_rejected(self) -> None:
        self.assertNotEqual(invoke("tag", "--tag=-danger", "--run-sha", SHA1).returncode, 0)
        self.assertNotEqual(
            invoke(
                "tag", "--tag", "v1.2.3", "--run-sha", SHA1, "--assigned-sha", "wrong"
            ).returncode,
            0,
        )

    def test_release_job_runs_on_main_push_and_manual_dispatch(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        events = workflow.split("on:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("  workflow_dispatch:", events)
        self.assertIn("  pull_request:", events)
        self.assertIn("  push:\n    branches: [main]", events)
        self.assertIn("github.event_name == 'push'", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("release_gate.py release", workflow)
        self.assertIn("release_gate.py tag", workflow)
        self.assertNotIn("--prerelease", workflow)

    def test_configuration_describes_existing_stack_not_proposed_clients(self) -> None:
        config = json.loads((ROOT / "repo.dfconfig").read_text(encoding="utf-8"))
        identity = config["repo"]["identity"]
        self.assertEqual(identity["development_branch"], "develop")
        self.assertEqual(identity["default_branch"], "develop")
        description = identity["description"].lower()
        self.assertIn("python", description)
        self.assertNotIn("react", description)
        self.assertNotIn("vercel", description)
        self.assertNotIn("typescript", identity["topics"])
        for unimplemented in ("server", "web", "desktop"):
            self.assertNotIn(unimplemented, config["repo"]["areas"])
        self.assertEqual(config["repo"]["versioning"]["mode"], "pridever")
        self.assertTrue(config["repo"]["protection"]["lanes"][0]["enforce_admins"])


if __name__ == "__main__":
    unittest.main()
