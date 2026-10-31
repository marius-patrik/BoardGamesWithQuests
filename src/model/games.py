"""Discover immutable bundled JSON game definitions, never executable rule plugins."""

from __future__ import annotations

from model.resources import bundled_games_root
import re

DEFAULT_GAME = "chess"


def available_games() -> list[str]:
    """Discover only validated source-controlled, packaged JSON definitions."""
    names: list[str] = []
    for entry in bundled_games_root().iterdir():
        if (
            entry.is_dir()
            and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", entry.name) is not None
            and entry.joinpath("config.json").is_file()
        ):
            names.append(entry.name)
    return sorted(names, key=lambda name: (name != DEFAULT_GAME, name))


def configuration_path(name: str) -> str:
    """Validate a bundled selector and return its inert resource identifier."""
    from model.definition import ConfigurationError, load_bundled_definition

    try:
        load_bundled_definition(name)
    except ConfigurationError as error:
        raise FileNotFoundError(f"no bundled game definition {name!r}") from error
    return name


def games_root() -> str:
    """Describe the installed games resource location for installation diagnostics."""
    return str(bundled_games_root())
