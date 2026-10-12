"""Locate independent sibling game packages via Python distribution entry points."""

from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import List, Optional

GROUP = "boardgameswithquests.games"


def _registered():
    """Yield playable game packages registered by this distribution."""
    try:
        installed = distribution("chesswithquests")
    except PackageNotFoundError:
        return
    for point in installed.entry_points:
        if point.group != GROUP:
            continue
        package = point.load()
        if getattr(package, "GAME_AVAILABLE", False):
            yield point.name, package


def available_games() -> List[str]:
    """List available game packages, placing the declared default first."""
    games = list(_registered())
    return [
        name
        for name, package in sorted(
            games, key=lambda pair: (not getattr(pair[1], "GAME_DEFAULT", False), pair[0])
        )
    ]


def default_configuration_name() -> Optional[str]:
    """Return the default playable package, or None."""
    names = available_games()
    return names[0] if names else None


def configuration_path(name: str) -> str:
    """Return the directory containing a registered, playable package.

    Args:
        name: Registered game package name.

    Returns:
        Absolute path to that game package.

    Raises:
        FileNotFoundError: The named package is not available.
    """
    for found, package in _registered():
        if found == name and getattr(package, "__file__", None):
            return str(Path(package.__file__).resolve().parent)
    raise FileNotFoundError(f"no playable game package named {name!r}")


def games_root() -> str:
    """Return the shared installation parent, not a separate games directory."""
    game = default_configuration_name()
    if game is None:
        raise FileNotFoundError("no playable game packages are installed")
    return str(Path(configuration_path(game)).parent)
