"""Run the shared engine with an installed game package."""

import argparse
import sys
from typing import Any, List, Optional

from engine.model.game.games import available_games, configuration_path, default_configuration_name


def build_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse game selection and diagnostic arguments."""
    parser = argparse.ArgumentParser(prog="chesswithquests")
    parser.add_argument("--game", default=None, help="name of the installed game package")
    parser.add_argument(
        "--check", action="store_true", help="report packages without opening a window"
    )
    return parser.parse_args(argv)


def report_installation() -> str:
    """Describe playable game packages in the distribution."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        current_version = version("chesswithquests")
    except PackageNotFoundError:
        current_version = "unknown"
    available = available_games()
    return (
        f"ChessWithQuests {current_version}\n"
        f"game packages: {', '.join(available) if available else '(none found)'}"
    )


def build_window(root: Any, game: Optional[str] = None) -> Any:
    """Construct the application through the engine view."""
    from engine.view.app import build_application

    return build_application(root, game)


def main(argv: Optional[List[str]] = None) -> int:
    """Open a game GUI, or show installed package diagnostics."""
    args = build_arguments(argv)
    if args.check:
        print(report_installation())
        return 0
    game = args.game or default_configuration_name()
    if not game:
        print("no playable game packages installed", file=sys.stderr)
        return 4
    try:
        configuration_path(game)
    except FileNotFoundError as error:
        print(str(error), file=sys.stderr)
        return 4
    try:
        import tkinter as tk
    except ImportError as error:
        print(f"tkinter is unavailable: {error}", file=sys.stderr)
        return 2
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"cannot open a window: {error}", file=sys.stderr)
        return 3
    try:
        window = build_window(root, game)
    except Exception as error:
        root.destroy()
        print(f"cannot start {game!r}: {error}", file=sys.stderr)
        return 4
    window.mainloop()
    return 0
