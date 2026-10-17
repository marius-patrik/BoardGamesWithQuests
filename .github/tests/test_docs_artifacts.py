"""Black-box CLI acceptance of artifact-backed documentation publication."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "collect_docs_artifacts.py"
ASSEMBLER = Path(__file__).resolve().parents[1] / "scripts" / "assemble_docs.py"
REPO = "marius-patrik/BoardGamesWithQuests"
GOOD = "a" * 40
STALE = "b" * 40


def run_record(number: int, name: str, branch: str, *, conclusion: str = "success"):
    return {
        "id": number,
        "name": name,
        "head_branch": branch,
        "event": "pull_request" if name == "Preview Documentation" else "push",
        "conclusion": conclusion,
        "repository": {"full_name": REPO},
    }


def artifact(number: int, name: str, run: int):
    return {"id": number, "name": name, "expired": False, "workflow_run": {"id": run}}


def prepare_cli(tmp: Path, fixtures: dict) -> dict[str, str]:
    """Run the real collector against an executable GitHub CLI protocol fixture."""
    root = tmp / "fixture"
    root.mkdir()
    (root / "github.json").write_text(json.dumps(fixtures), encoding="utf-8")
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    executable = bin_dir / "gh"
    executable.write_text(
        "#!" + sys.executable + "\n"
        "import json,os,sys,shutil,pathlib,urllib.parse\n"
        "f=json.loads(pathlib.Path(os.environ['GH_FIXTURES']).read_text())\n"
        "a=sys.argv[1:]\n"
        "if a[0]=='api':\n"
        " p=urllib.parse.urlsplit(a[1]); q=urllib.parse.parse_qs(p.query)\n"
        " if p.path.endswith('/pulls'): obj=f['prs']\n"
        " elif p.path.endswith('/actions/artifacts'):\n"
        "  obj={'artifacts': f['artifacts'].get(q['name'][0],[])}\n"
        " elif '/actions/runs/' in p.path:\n"
        "  obj=f['runs'][p.path.rsplit('/',1)[-1]]\n"
        " else: sys.exit(7)\n"
        " print(json.dumps(obj))\n"
        "elif a[:2]==['run','download']:\n"
        " n=a[a.index('--name')+1]; d=pathlib.Path(a[a.index('--dir')+1])\n"
        " src=pathlib.Path(os.environ['GH_FIXTURES']).parent/n\n"
        " if not src.exists(): sys.exit(6)\n"
        " shutil.copytree(src,d,dirs_exist_ok=True)\n"
        "else: sys.exit(8)\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return {
        **os.environ,
        "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
        "GH_FIXTURES": str(root / "github.json"),
    }


def snapshot(tmp: Path, name: str, html: str, sha: str | None = None) -> None:
    dest = tmp / "fixture" / name
    dest.mkdir()
    (dest / "index.html").write_text(html, encoding="utf-8")
    if sha is not None:
        (dest / ".preview-head").write_text(sha, encoding="utf-8")
    (dest / ".nojekyll").touch()


def invoke(tmp: Path, env: dict[str, str]):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", REPO, "--staging", str(tmp / "staging")],
        env=env,
        capture_output=True,
        text=True,
    )


def assemble(tmp: Path, *prs: int):
    return subprocess.run(
        [
            sys.executable, str(ASSEMBLER),
            "--staging", str(tmp / "staging"),
            "--site", str(tmp / "site"), "--open-prs", *(str(p) for p in prs),
        ],
        capture_output=True,
        text=True,
    )


def test_main_and_matching_pr_publish_without_branch_storage(tmp_path: Path) -> None:
    env = prepare_cli(
        tmp_path,
        {
            "prs": [
                {
                    "number": 331,
                    "head": {
                        "sha": GOOD, "ref": "topic",
                        "repo": {"full_name": REPO},
                    },
                },
                {
                    "number": 339,
                    "head": {
                        "sha": GOOD, "ref": "fork",
                        "repo": {"full_name": "elsewhere/other"},
                    },
                },
            ],
            "artifacts": {
                "docs-main": [artifact(1, "docs-main", 10)],
                "docs-preview-331": [
                    artifact(2, "docs-preview-331", 11),
                    artifact(3, "docs-preview-331", 12),
                ],
            },
            "runs": {
                "10": run_record(10, "Build Main Documentation", "main"),
                "11": run_record(11, "Preview Documentation", "topic"),
                "12": run_record(12, "Preview Documentation", "topic"),
            },
        },
    )
    snapshot(tmp_path, "docs-main", "<h1>Passing main</h1>")
    snapshot(tmp_path, "docs-preview-331", "<h1>PR head</h1>", GOOD)
    collected = invoke(tmp_path, env)
    assert collected.returncode == 0, collected.stderr
    result = assemble(tmp_path, 331)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "site/index.html").read_text() == "<h1>Passing main</h1>"
    assert (tmp_path / "site/pr-331/index.html").read_text() == "<h1>PR head</h1>"
    assert not (tmp_path / "site/pr-339").exists()


def test_failed_main_and_outdated_pr_never_publish_stale_content(tmp_path: Path) -> None:
    env = prepare_cli(
        tmp_path,
        {
            "prs": [
                {
                    "number": 331,
                    "head": {
                        "sha": GOOD, "ref": "topic",
                        "repo": {"full_name": REPO},
                    },
                },
            ],
            "artifacts": {
                "docs-main": [artifact(1, "docs-main", 10)],
                "docs-preview-331": [artifact(2, "docs-preview-331", 11)],
            },
            "runs": {
                "10": run_record(
                    10, "Build Main Documentation", "main", conclusion="failure"
                ),
                "11": run_record(11, "Preview Documentation", "topic"),
            },
        },
    )
    snapshot(tmp_path, "docs-main", "<h1>Failed main</h1>")
    snapshot(tmp_path, "docs-preview-331", "<h1>Old PR</h1>", STALE)
    collected = invoke(tmp_path, env)
    assert collected.returncode == 0, collected.stderr
    result = assemble(tmp_path, 331)
    assert result.returncode == 0, result.stderr
    content = (tmp_path / "site/index.html").read_text()
    assert "production documentation build is unavailable" in content.lower()
    assert not (tmp_path / "site/pr-331").exists()
    assert "Old PR" not in content
    assert "Failed main" not in content


@pytest.mark.parametrize(
    "workflow,branch", [
        ("Another Workflow", "topic"),
        ("Preview Documentation", "other-branch"),
    ],
)
def test_spoofed_artifact_origin_is_rejected(
    tmp_path: Path, workflow: str, branch: str,
) -> None:
    env = prepare_cli(
        tmp_path,
        {
            "prs": [
                {
                    "number": 331,
                    "head": {
                        "sha": GOOD, "ref": "topic",
                        "repo": {"full_name": REPO},
                    },
                },
            ],
            "artifacts": {
                "docs-preview-331": [artifact(3, "docs-preview-331", 15)],
            },
            "runs": {"15": run_record(15, workflow, branch)},
        },
    )
    snapshot(tmp_path, "docs-preview-331", "<h1>Forged</h1>", GOOD)
    result = invoke(tmp_path, env)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "staging/pr-331").exists()


def test_github_api_failure_does_not_claim_success(tmp_path: Path) -> None:
    env = prepare_cli(tmp_path, {"prs": [], "artifacts": {}, "runs": {}})
    (tmp_path / "fixture/github.json").write_text("{", encoding="utf-8")
    result = invoke(tmp_path, env)
    assert result.returncode != 0
    assert not (tmp_path / "staging/index.html").exists()
