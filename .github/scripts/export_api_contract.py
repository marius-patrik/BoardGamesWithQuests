#!/usr/bin/env python3
"""Extract the single normative OpenAPI 3.1 YAML from API.md for tooling."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / ".agents/requirements/notes/API.md"


def extract() -> str:
    """Return exactly the YAML contents of the one fenced contract."""
    text = SOURCE.read_text(encoding="utf-8")
    matches = re.findall(r"(?ms)^\x60{3}yaml\n(.*?)\n\x60{3}\s*$", text)
    if len(matches) != 1:
        raise ValueError("API.md must have exactly one normative YAML code block")
    content = matches[0] + chr(10)
    document = yaml.safe_load(content)
    if not isinstance(document, dict) or not str(document.get("openapi", "")).startswith("3.1."):
        raise ValueError("API.md does not contain OpenAPI 3.1")
    return content


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination == SOURCE or destination.is_relative_to(ROOT / ".agents"):
        parser.error("contract source must never be overwritten")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(extract(), encoding="utf-8")
