"""Real editable, wheel and sdist product acceptance outside the source checkout.

This standalone integration test builds installable artifacts and validates the
public installed CLI, rules, authoritative transitions and durable saved games.
It runs in a dedicated CI job, not as an implementation-mocked unit test.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[2]
CHECK_SCRIPT = r"""
import hashlib
from importlib import metadata
import json
from pathlib import Path
import sys
from model.games import available_games
from model.resources import bundled_games_root
from model.session import DesktopSession
from model.persistence import load_session, save_session

saved_dir = Path(sys.argv[1])
phase = sys.argv[2]
source_root = Path(sys.argv[3])
installation = sys.argv[4]
import boardgameswithquests
if installation != "editable" and Path(boardgameswithquests.__file__).resolve().is_relative_to(source_root):
    raise AssertionError("installed wheel/sdist imported source checkout")
if metadata.version("boardgameswithquests") != "1.0.0":
    raise AssertionError("distribution metadata version mismatch")
games = available_games()
if games != ["chess", "checkers"]:
    raise AssertionError(f"unexpected game catalog {games}")
for name in games:
    resource = bundled_games_root().joinpath(name).joinpath("config.json")
    installed = resource.read_bytes()
    source = (source_root / "games" / name / "config.json").read_bytes()
    if hashlib.sha256(installed).digest() != hashlib.sha256(source).digest():
        raise AssertionError(f"altered installed {name} rulebook")
    path = saved_dir / (name + ".json")
    if phase == "create":
        session = DesktopSession(name)
        opening = session.snapshot()
        actions = session.legal_actions()
        if not actions:
            raise AssertionError(f"{name}: no legal opening action")
        actor = opening["participants"][str(opening["active_side"])]
        request = {"type": "move", "move": actions[0]}
        accepted = session.submit(actor, opening["revision"], request, action_id="installed-acceptance")
        if accepted["state"]["revision"] != opening["revision"] + 1:
            raise AssertionError("revision failed to advance once")
        retry = session.submit(actor, opening["revision"], request, action_id="installed-acceptance")
        if retry["event"] != accepted["event"]:
            raise AssertionError("idempotent retry failed")
        if DesktopSession.recover(accepted["state"]).snapshot() != accepted["state"]:
            raise AssertionError("snapshot replay diverged")
        save_session(session, path)
        session.reset("checkers" if name == "chess" else "chess")
        if not session.legal_actions():
            raise AssertionError("game switching lost legal actions")
    else:
        session = load_session(path)
        if session.snapshot()["revision"] != 1:
            raise AssertionError("persisted revision changed after restart")
        if DesktopSession.recover(session.snapshot()).snapshot() != session.snapshot():
            raise AssertionError("reopened snapshot replay diverged")
print(f"{installation} {phase} PASS")
"""


def run(args: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, timeout=240)
    if result.returncode:
        raise AssertionError(
            f"command {args!r} failed with {result.returncode}:\n"
            f"{result.stdout}\n{result.stderr}"
        )
    print(result.stdout.strip())


def verify(name: str, install_target: str, workspace: Path, env: dict[str, str]) -> None:
    venv_dir = workspace / (name + "-venv")
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    install = [str(python), "-m", "pip", "install", "--no-deps"]
    if name == "editable":
        install.append("-e")
    install.append(install_target)
    run(install, cwd=workspace, env=env)
    run([str(python), "-m", "boardgameswithquests", "--check"], cwd=workspace, env=env)
    executable = venv_dir / ("Scripts/boardgameswithquests.exe" if os.name == "nt" else "bin/boardgameswithquests")
    run([str(executable), "--check"], cwd=workspace, env=env)
    records = workspace / (name + "-saves")
    records.mkdir()
    for phase in ("create", "reopen"):
        run([str(python), "-c", CHECK_SCRIPT, str(records), phase, str(ROOT), name], cwd=workspace, env=env)


def main() -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["SETUPTOOLS_SCM_PRETEND_VERSION"] = "1.0.0"
    with tempfile.TemporaryDirectory(prefix="bgw-installed-") as scratch:
        work = Path(scratch)
        output = work / "artifacts"
        output.mkdir()
        run(
            [sys.executable, "-m", "build", "--wheel", "--sdist", "--outdir", str(output)],
            cwd=ROOT,
            env=environment,
        )
        wheels = list(output.glob("*.whl"))
        sdists = list(output.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise AssertionError("expected exactly one wheel and one sdist")
        verify("editable", str(ROOT), work, environment)
        # Explicit editable invocation without modifying the cloned checkout.
        verify("wheel", str(wheels[0]), work, environment)
        verify("sdist", str(sdists[0]), work, environment)


if __name__ == "__main__":
    main()
