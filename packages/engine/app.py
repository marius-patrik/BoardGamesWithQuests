"""Engine entry point. The complete GUI is delivered in a later feature PR."""

import argparse
import sys
from typing import Any, List, Optional

from engine.model.game.configuration import (
    ConfigurationError,
    installed_definitions,
    named_definition,
)
from engine.model.game.games import default_configuration_name


def build_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse game selection and installation diagnostics."""
    parser = argparse.ArgumentParser(prog="chesswithquests")
    parser.add_argument("--game", default=None, help="registered game package")
    parser.add_argument("--check", action="store_true", help="inspect packages without a GUI")
    return parser.parse_args(argv)


def report_installation() -> str:
    """Report installed game packages and whether gameplay has been implemented."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        current_version = version("chesswithquests")
    except PackageNotFoundError:
        current_version = "unknown"
    lines = [f"ChessWithQuests {current_version}", "game packages:"]
    for game in installed_definitions():
        lines.append(
            f"  {game.name}: {game.title} ({'ready' if game.playable else 'not implemented'})"
        )
    return "\n".join(lines)


def build_window(root: Any, game: str) -> Any:
    """Delegate to the actual application view, not a placeholder shell."""
    from engine.view.app import build_application

    return build_application(root, game)


def main(argv: Optional[List[str]] = None) -> int:
    """Inspect installed games or launch the fully implemented application."""
    args = build_arguments(argv)
    try:
        if args.check:
            print(report_installation())
            return 0
        name = args.game or default_configuration_name()
        if name is None:
            raise ConfigurationError("no default game is registered")
        game = named_definition(name)
        if not game.playable:
            print(f"{game.title} is not implemented yet", file=sys.stderr)
            return 4
    except ConfigurationError as error:
        print(f"invalid game configuration: {error}", file=sys.stderr)
        return 4

    try:
        import tkinter as tk
    except ImportError as error:
        print(f"tkinter unavailable: {error}", file=sys.stderr)
        return 2
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"cannot open a window: {error}", file=sys.stderr)
        return 3
    try:
        window = build_window(root, game.name)
    except (ImportError, AttributeError) as error:
        root.destroy()
        print(f"full application view has not been implemented: {error}", file=sys.stderr)
        return 4
    window.mainloop()
    return 0
