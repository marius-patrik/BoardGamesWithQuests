"""Headless package inspection entry point; the user interface runs on the web."""

import argparse
import sys
from typing import List, Optional

from engine.model.game.configuration import ConfigurationError, installed_definitions


def build_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse inspection options without exposing a non-existent local GUI."""
    parser = argparse.ArgumentParser(prog="boardgameswithquests")
    parser.add_argument("--check", action="store_true", help="inspect installed game definitions")
    return parser.parse_args(argv)


def report_installation() -> str:
    """Describe installed games without implying working gameplay."""
    lines = ["BoardGamesWithQuests game packages:"]
    for game in installed_definitions():
        state = "ready" if game.playable else "not implemented"
        lines.append(f"  {game.name}: {game.title} ({state})")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """Check definitions or explicitly reject unsupported headless gameplay."""
    args = build_arguments(argv)
    try:
        if args.check:
            print(report_installation())
            return 0
    except ConfigurationError as error:
        print(f"Invalid configuration: {error}", file=sys.stderr)
        return 4
    print("No local GUI exists. Gameplay requires the web/API application.", file=sys.stderr)
    return 4
