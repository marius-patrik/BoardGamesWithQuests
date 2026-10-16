"""Exercise the supplemental contract CLI with real bundled JSON variants."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("variant", ["declared-rules", "alternate-opening", "malformed"])
def test_contract_probe_consumes_rules_and_configured_opening(tmp_path, variant):
    """Valid game data executes; corrupted external configuration fails the CLI."""
    package = tmp_path / "english_draughts"
    package.mkdir()
    (package / "__init__.py").write_text('"""Isolated declared game resource."""\n')
    data = json.loads((ROOT / "packages/english_draughts/config.json").read_text())
    if variant == "alternate-opening":
        data["starting_side"] = 1
    elif variant == "malformed":
        data["starting_side"] = True
    (package / "config.json").write_text(json.dumps(data))
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/probe_json_contract.py")],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": os.pathsep.join((str(tmp_path), str(ROOT / "packages")))},
        capture_output=True,
        text=True,
    )
    if variant == "malformed":
        assert result.returncode != 0 and "ConfigurationError" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert "per-participant quest isolation probes passed" in result.stdout
