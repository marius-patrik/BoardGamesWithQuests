"""The application entry point.

`python -m boardgameswithquests` starts the application. This module owns the process: it
parses the command line, opens the window and runs the event loop. Everything it shows is
built by `view/`, and the rules it plays are the ones the selected configuration declares.
"""

import argparse
import sys
from typing import Any, List, Optional

from model.games import DEFAULT_GAME, available_games, configuration_path, games_root

__all__ = ["main", "build_window"]

APPLICATION_TITLE = "BoardGamesWithQuests"


def build_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse the command line.

    `--check` is what makes the entry point verifiable without a display: it reports what
    the installation can find and exits, so continuous integration can exercise the whole
    startup path on a machine with no window server.

    Args:
        argv: Argument list to parse. Defaults to `sys.argv[1:]`.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="boardgameswithquests",
        description="Play a board game from a configuration.",
    )
    parser.add_argument(
        "--game",
        default=DEFAULT_GAME,
        help="name of the configuration to play (default: %(default)s)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what this installation can find, then exit without opening a window",
    )
    return parser.parse_args(argv)


def report_installation() -> str:
    """Describe what this installation can find.

    Returns:
        str: A report naming the located `games/` directory and every shipped
        configuration.
    """
    from model.session import DesktopSession

    games = available_games()
    if not games or DEFAULT_GAME not in games:
        raise ValueError("bundled games are missing")
    # This is an installed-product diagnostic, not an alternate gameplay engine.
    # Resolve each bundled JSON rulebook from the installed runtime and run a
    # real accepted action through the same local session used by Tkinter.
    for name in games:
        session = DesktopSession(name)
        opening = session.snapshot()
        moves = session.legal_actions()
        if not moves:
            raise ValueError(f"{name}: no playable opening actions")
        actor = opening["participants"][str(opening["active_side"])]
        request = {"type": "move", "move": moves[0]}
        accepted = session.submit(
            actor, opening["revision"], request, action_id="installation-check"
        )
        if accepted["state"]["revision"] != opening["revision"] + 1:
            raise ValueError(f"{name}: transition did not commit exactly once")
        if (
            session.submit(actor, opening["revision"], request, action_id="installation-check")[
                "event"
            ]
            != accepted["event"]
        ):
            raise ValueError(f"{name}: identical action retry is not idempotent")
        if DesktopSession.recover(accepted["state"]).snapshot() != accepted["state"]:
            raise ValueError(f"{name}: installed session does not replay")
    lines = [
        f"{APPLICATION_TITLE} {_version()}",
        f"games directory: {games_root()}",
        f"configurations: {', '.join(games)}",
        f"accepted and replayed opening moves: {len(games)}",
    ]
    return "\n".join(lines)


def _version() -> str:
    """Return the installed distribution version, or `unknown` when running uninstalled.

    Returns:
        str: The distribution version string.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python 3.7 and older
        return "unknown"
    try:
        return version("boardgameswithquests")
    except PackageNotFoundError:
        return "unknown"


def build_window(root: Any, game: str = DEFAULT_GAME):
    """Populate a Tk root with the application window.

    Args:
        root: The `tkinter.Tk` instance to build into.
        game: Name of the configuration to start.

    Returns:
        tkinter.Toplevel or the root: The window the game is shown in.
    """
    from view.app import build_application

    return build_application(root, game)


def main(argv: Optional[List[str]] = None) -> int:
    """Start the application.

    Args:
        argv: Argument list to parse. Defaults to `sys.argv[1:]`.

    Returns:
        int: The process exit code. Zero on a clean exit, non-zero on failure.

    Raises:
        SystemExit: Never raised by this function; the exit code is returned instead so a
            caller can drive it from a test.
    """
    args = build_arguments(argv)

    if args.check:
        try:
            report = report_installation()
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            if sys.stderr is not None:
                print(f"installation check failed: {error}", file=sys.stderr)
            return 5
        if sys.stdout is not None:
            print(report)
        return 0

    try:
        configuration_path(args.game)
    except FileNotFoundError as error:
        print(str(error), file=sys.stderr)
        return 4

    try:
        import tkinter as tk
    except ImportError as error:  # pragma: no cover - depends on the interpreter build
        print(f"tkinter is unavailable: {error}", file=sys.stderr)
        return 2

    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"cannot open a window: {error}", file=sys.stderr)
        return 3

    try:
        window = build_window(root, args.game)
    except Exception as error:
        root.destroy()
        print(f"cannot start {args.game!r}: {error}", file=sys.stderr)
        return 4

    window.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
