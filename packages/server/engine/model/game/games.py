"""Game discovery, backed by sibling game package config.json files."""

from importlib import resources
from pathlib import Path
from typing import List, Optional

from engine.model.game.configuration import installed_definitions, named_definition


def available_games() -> List[str]:
    """List registered game packages, including incomplete implementations."""
    return [game.name for game in installed_definitions()]


def default_configuration_name() -> Optional[str]:
    """Return declared default game package, if any."""
    return next((game.name for game in installed_definitions() if game.default), None)


def configuration_path(name: str) -> str:
    """Return a registered package directory, not a games/ subfolder."""
    named_definition(name)
    return str(Path(str(resources.files(name))).resolve())


def games_root() -> str:
    """Return the parent containing the installed sibling game packages."""
    default = default_configuration_name()
    if default is None:
        raise FileNotFoundError("no game package declares itself default")
    return str(Path(configuration_path(default)).parent)
