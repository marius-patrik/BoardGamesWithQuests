"""Exercise CI acceptance through real CLI inputs, execution evidence and failures."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

GATE = Path(__file__).parents[1] / ".github/scripts/verify_quality_gate.py"


def detected_plan() -> dict:
    """Represent the executable report emitted by the pinned DarkFactory CLI."""
    actions = [
        ("python", ".", "test", version, "pytest") for version in ("3.10", "3.11", "3.12", "3.13")
    ] + [
        ("python", ".", "format_check", "", "black --check --line-length 100 ."),
        ("rust", "packages/desktop/src-tauri", "test", "", "cargo test --all-features --workspace"),
        (
            "rust",
            "packages/desktop/src-tauri",
            "lint",
            "",
            "cargo clippy --workspace --all-targets --all-features -- -D warnings",
        ),
        ("rust", "packages/desktop/src-tauri", "format_check", "", "cargo fmt --all -- --check"),
        ("node", "packages/web", "typecheck", "", "bun run typecheck"),
        ("node", "packages/web", "lint", "", "biome lint ."),
        ("node", "packages/web", "format_check", "", "biome ci ."),
    ]
    return {
        "matrix": [
            {
                "id": f"{ecosystem}:{cwd}:{kind}{'@' + version if version else ''}",
                "packageId": f"{ecosystem}:{cwd}",
                "ecosystem": ecosystem,
                "cwd": cwd,
                "kind": kind,
                "version": version,
                "command": command,
            }
            for ecosystem, cwd, kind, version, command in actions
        ],
        "gaps": [{"packageId": "node:packages/web", "kind": "test", "supported": False}],
    }


def evidence(tmp_path: Path, plan: dict | None = None) -> tuple[Path, Path]:
    """Create a valid discovery report and successful action artifacts."""
    plan = detected_plan() if plan is None else plan
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "tests/test_actor.py").write_text(
        "def test_file_roundtrip(tmp_path):\n    path = tmp_path / 'state.txt'\n    path.write_text('committed')\n    assert path.read_text() == 'committed'\n"
    )
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    results = tmp_path / "results"
    results.mkdir(exist_ok=True)
    for index, action in enumerate(plan["matrix"]):
        folder = results / str(index)
        folder.mkdir(exist_ok=True)
        (folder / "result.json").write_text(json.dumps({"id": action["id"], "result": "success"}))
    return path, results


def run_gate(
    tmp_path: Path, path: Path, results: Path | None = None
) -> subprocess.CompletedProcess:
    """Invoke the same standalone Python CLI that CI executes."""
    args = [sys.executable, str(GATE), "--repo", str(tmp_path), "--plan", str(path)]
    if results is not None:
        args.extend(["--results", str(results)])
    return subprocess.run(args, capture_output=True, text=True, check=False)


def test_complete_discovery_and_actual_success_reports_are_accepted(tmp_path: Path) -> None:
    path, results = evidence(tmp_path)
    assert run_gate(tmp_path, path).returncode == 0
    result = run_gate(tmp_path, path, results)
    assert result.returncode == 0 and "Accepted 11 quality actions" in result.stdout


@pytest.mark.parametrize(
    "ecosystem,kind,version",
    [
        ("python", "test", "3.10"),
        ("python", "test", "3.11"),
        ("python", "test", "3.12"),
        ("python", "test", "3.13"),
        ("python", "format_check", ""),
        ("rust", "test", ""),
        ("rust", "lint", ""),
        ("rust", "format_check", ""),
        ("node", "typecheck", ""),
        ("node", "lint", ""),
        ("node", "format_check", ""),
    ],
)
def test_missing_mandatory_action_cannot_publish_green_status(
    tmp_path: Path, ecosystem: str, kind: str, version: str
) -> None:
    plan = detected_plan()
    plan["matrix"] = [
        action
        for action in plan["matrix"]
        if (action["ecosystem"], action["kind"], action["version"]) != (ecosystem, kind, version)
    ]
    path, results = evidence(tmp_path, plan)
    result = run_gate(tmp_path, path, results)
    assert result.returncode == 1 and "missing mandatory quality action" in result.stderr


def test_empty_matrix_cannot_pass_when_quality_runner_was_skipped(tmp_path: Path) -> None:
    path, results = evidence(tmp_path, {"matrix": [], "gaps": []})
    assert run_gate(tmp_path, path, results).returncode == 1


@pytest.mark.parametrize("command", ["", "echo tests passed", "pytest --collect-only", "true"])
def test_replaced_python_behavior_command_is_rejected(tmp_path: Path, command: str) -> None:
    plan = detected_plan()
    plan["matrix"][0]["command"] = command
    path, results = evidence(tmp_path, plan)
    assert run_gate(tmp_path, path, results).returncode == 1


@pytest.mark.parametrize("status", ["failure", "skipped", "cancelled", None])
def test_failed_or_unexecuted_action_cannot_publish_green_status(
    tmp_path: Path, status: str | None
) -> None:
    path, results = evidence(tmp_path)
    report = results / "0/result.json"
    if status is None:
        report.unlink()
    else:
        payload = json.loads(report.read_text())
        payload["result"] = status
        report.write_text(json.dumps(payload))
    result = run_gate(tmp_path, path, results)
    assert result.returncode == 1 and "did not execute successfully" in result.stderr


def test_missing_permanent_python_tests_cannot_pass(tmp_path: Path) -> None:
    path, results = evidence(tmp_path)
    (tmp_path / "tests/test_actor.py").unlink()
    result = run_gate(tmp_path, path, results)
    assert result.returncode == 1 and "behavioral tests were not discovered" in result.stderr


def test_mandatory_unsupported_gap_overrides_an_apparently_present_action(tmp_path: Path) -> None:
    plan = detected_plan()
    plan["gaps"].append({"packageId": "rust:packages/desktop/src-tauri", "kind": "test"})
    path, results = evidence(tmp_path, plan)
    result = run_gate(tmp_path, path, results)
    assert result.returncode == 1 and "reported as unsupported" in result.stderr


@pytest.mark.parametrize("duplicate", [True, False])
def test_duplicate_or_unknown_execution_evidence_is_rejected(
    tmp_path: Path, duplicate: bool
) -> None:
    path, results = evidence(tmp_path)
    payload = json.loads((results / "0/result.json").read_text())
    if not duplicate:
        payload["id"] = "unknown:check"
    (results / "extra").mkdir()
    (results / "extra/result.json").write_text(json.dumps(payload))
    assert run_gate(tmp_path, path, results).returncode == 1


@pytest.mark.parametrize("payload", [[], {"gaps": []}, {"matrix": "missing", "gaps": []}])
def test_malformed_provider_reports_fail_with_specific_rejection(
    tmp_path: Path, payload: object
) -> None:
    path, results = evidence(tmp_path)
    path.write_text(json.dumps(payload))
    result = run_gate(tmp_path, path, results)
    assert result.returncode == 1 and "Quality gate rejected" in result.stderr


def test_recorded_runner_failure_is_consumed_without_conversion_to_success(tmp_path: Path) -> None:
    path, results = evidence(tmp_path)
    action = detected_plan()["matrix"][0]["id"]
    recording = subprocess.run(
        [
            sys.executable,
            str(GATE),
            "--record",
            str(results / "0/result.json"),
            "--id",
            action,
            "--result",
            "failure",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert recording.returncode == 0
    assert run_gate(tmp_path, path, results).returncode == 1


def test_duplicate_provider_fields_cannot_hide_mandatory_gaps(tmp_path: Path) -> None:
    path, results = evidence(tmp_path)
    serialized = path.read_text()
    path.write_text(serialized[:-1] + ', "gaps": []}')
    result = run_gate(tmp_path, path, results)
    assert result.returncode == 1 and "duplicate report field" in result.stderr


def test_malformed_gap_does_not_become_an_optional_success(tmp_path: Path) -> None:
    plan = detected_plan()
    plan["gaps"] = [{"packageId": "python:."}]
    path, results = evidence(tmp_path, plan)
    assert run_gate(tmp_path, path, results).returncode == 1


def installation_fixture(tmp_path: Path) -> None:
    """Create an actual immutable workflow and a receipt over its exact bytes."""
    import hashlib

    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    (tmp_path / ".darkfactory").mkdir()
    revision = "a" * 40
    config = {"repo": {"upstream": {"ref": revision}}}
    (tmp_path / "repo.dfconfig").write_text(json.dumps(config))
    (workflows / "darkfactory-control.yml").write_text(
        "jobs:\n  verify:\n    steps:\n      - uses: vendor/action@" + revision + "\n"
    )
    hashes = {
        path: hashlib.sha256((tmp_path / path).read_bytes()).hexdigest()
        for path in ("repo.dfconfig", ".github/workflows/darkfactory-control.yml")
    }
    (tmp_path / ".darkfactory/installation.json").write_text(
        json.dumps({"release": {"sha": revision}, "fileHashes": hashes})
    )


def test_installation_cli_accepts_coherent_bytes_and_immutable_dependencies(tmp_path):
    installation_fixture(tmp_path)
    result = subprocess.run(
        [sys.executable, str(GATE), "--installation", "--repo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "fault", ["config", "controller", "pin", "mutable", "missing", "escape", "runtime"]
)
def test_installation_cli_rejects_drift_and_unsafe_workflow_inputs(tmp_path, fault):
    installation_fixture(tmp_path)
    if fault == "config":
        with (tmp_path / "repo.dfconfig").open("a") as stream:
            stream.write("\n")
    elif fault == "controller":
        with (tmp_path / ".github/workflows/darkfactory-control.yml").open("a") as stream:
            stream.write("# changed\n")
    elif fault == "pin":
        path = tmp_path / ".darkfactory/installation.json"
        receipt = json.loads(path.read_text())
        receipt["release"]["sha"] = "b" * 40
        path.write_text(json.dumps(receipt))
    elif fault == "missing":
        (tmp_path / ".darkfactory/installation.json").unlink()
    else:
        target = "vendor/action@v1" if fault == "mutable" else "./../outside/action"
        if fault == "runtime":
            target = "marius-patrik/DarkFactory/.github/workflows/agent.yml@" + "b" * 40
        (tmp_path / ".github/workflows/extra.yml").write_text(
            "jobs:\n  probe:\n    uses: " + target + "\n"
        )
    before = {str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    result = subprocess.run(
        [sys.executable, str(GATE), "--installation", "--repo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1 and "rejected" in result.stderr
    assert {
        str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    } == before


@pytest.mark.parametrize("branch", ["feature/format", "review/$(touch injected)", "main"])
def test_formatter_push_preserves_literal_branch_and_protects_default(tmp_path, branch):
    """Execute the workflow shell against hostile branch data and a Git boundary."""
    import os

    workflow = (GATE.parents[1] / "workflows/auto-format.yml").read_text()
    step = workflow.split("      - name: Commit tracked formatting changes\n", 1)[1]
    script = "\n".join(line[10:] for line in step.split("        run: |\n", 1)[1].splitlines())
    git = tmp_path / "git"
    git.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = diff ]; then exit 1; fi\n'
        'if [ "$1" = push ]; then printf "%s\\n" "$@" > "$PUSH_LOG"; fi\n'
    )
    git.chmod(0o755)
    log = tmp_path / "push.log"
    result = subprocess.run(
        ["bash", "-e", "-c", script],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "FORMAT_BRANCH": branch,
            "DEFAULT_BRANCH": "main",
            "PUSH_LOG": str(log),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "injected").exists()
    if branch == "main":
        assert not log.exists()
    else:
        assert log.read_text().splitlines() == ["push", "origin", f"HEAD:{branch}"]
