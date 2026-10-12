"""Validated JSON game configuration. Rules and quests remain code extensions."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from importlib.metadata import entry_points
import json
from typing import Any

GROUP = "boardgameswithquests.games"


class ConfigurationError(ValueError):
    """The installed game's declarative settings are invalid."""


@dataclass(frozen=True)
class GameDefinition:
    """Immutable metadata for a game implementation package."""

    name: str
    package: str
    title: str
    default: bool
    playable: bool
    board: dict[str, Any]
    pieces: dict[str, dict[str, Any]]
    clock: dict[str, Any]
    exports: tuple[str, ...]
    appearance: dict[str, Any]


def load_definition(package: str) -> GameDefinition:
    """Load a sibling package's root config.json without loading rules or quests."""
    try:
        data = json.loads(resources.files(package).joinpath("config.json").read_text("utf-8"))
    except (ModuleNotFoundError, OSError, ValueError) as error:
        raise ConfigurationError(f"{package}: missing or invalid config.json: {error}") from error
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ConfigurationError(f"{package}: unsupported config schema version")
    name, title = data.get("name"), data.get("title")
    if not all(isinstance(v, str) and v for v in (name, title)):
        raise ConfigurationError(f"{package}: name and title must be strings")
    if not all(type(data.get(v)) is bool for v in ("default", "playable")):
        raise ConfigurationError(f"{package}: default and playable must be booleans")
    board = data.get("board")
    if not isinstance(board, dict):
        raise ConfigurationError(f"{package}: missing board definition")
    rows, cols = board.get("rows"), board.get("columns")
    if not all(type(v) is int and 1 <= v <= 256 for v in (rows, cols)):
        raise ConfigurationError(f"{package}: board dimensions are invalid")
    pieces = data.get("pieces")
    if not isinstance(pieces, dict) or not pieces:
        raise ConfigurationError(f"{package}: pieces must be a nonempty object")
    for key, piece in pieces.items():
        if not isinstance(key, str) or not isinstance(piece, dict):
            raise ConfigurationError(f"{package}: malformed piece")
        symbols = piece.get("symbols")
        if not isinstance(symbols, dict) or any(
            not isinstance(symbols.get(color), str) or not symbols[color]
            for color in ("white", "black")
        ):
            raise ConfigurationError(f"{package}: {key} needs white and black symbols")
        for kind in ("moves", "attacks"):
            vectors = piece.get(kind)
            if (
                not isinstance(vectors, list)
                or not vectors
                or any(
                    not isinstance(v, list)
                    or len(v) != 2
                    or any(type(axis) is not int for axis in v)
                    or v == [0, 0]
                    for v in vectors
                )
            ):
                raise ConfigurationError(f"{package}: {key}.{kind} has invalid vectors")
        if any(type(piece.get(prop)) is not bool for prop in ("jump", "repeat")):
            raise ConfigurationError(f"{package}: {key} requires jump/repeat booleans")
    placements = board.get("starting_pieces")
    if not isinstance(placements, list):
        raise ConfigurationError(f"{package}: starting_pieces must be a list")
    occupied: set[tuple[int, int]] = set()
    for placement in placements:
        if not isinstance(placement, dict) or placement.get("piece") not in pieces:
            raise ConfigurationError(f"{package}: unknown piece in starting position")
        if placement.get("color") not in ("white", "black"):
            raise ConfigurationError(f"{package}: invalid team")
        squares = placement.get("squares")
        if not isinstance(squares, list):
            raise ConfigurationError(f"{package}: starting squares must be a list")
        for square in squares:
            if (
                not isinstance(square, list)
                or len(square) != 2
                or any(type(axis) is not int for axis in square)
                or not (0 <= square[0] < rows and 0 <= square[1] < cols)
            ):
                raise ConfigurationError(f"{package}: invalid square {square!r}")
            if tuple(square) in occupied:
                raise ConfigurationError(f"{package}: duplicate square {square!r}")
            occupied.add(tuple(square))
    clock = data.get("clock")
    if not isinstance(clock, dict) or any(
        type(clock.get(key)) is not int or clock[key] < 0
        for key in ("initial_seconds", "increment_seconds")
    ):
        raise ConfigurationError(f"{package}: invalid clock")
    exports = data.get("exports", [])
    if not isinstance(exports, list) or any(not isinstance(v, str) for v in exports):
        raise ConfigurationError(f"{package}: invalid exports")
    appearance = data.get("appearance", {})
    if not isinstance(appearance, dict):
        raise ConfigurationError(f"{package}: invalid appearance")
    return GameDefinition(
        name,
        package,
        title,
        data["default"],
        data["playable"],
        board,
        pieces,
        clock,
        tuple(exports),
        appearance,
    )


def installed_definitions() -> list[GameDefinition]:
    """Discover game packages via entry points, without a game-name registry."""
    found: dict[str, GameDefinition] = {}
    for plugin in entry_points(group=GROUP):
        config = load_definition(plugin.value.split(":", 1)[0])
        if plugin.name != config.name or config.name in found:
            raise ConfigurationError(f"invalid or duplicated game registration: {plugin.name}")
        found[config.name] = config
    if sum(game.default for game in found.values()) > 1:
        raise ConfigurationError("multiple default games declared")
    return sorted(found.values(), key=lambda game: (not game.default, game.name))


def board_from_definition(definition: GameDefinition):
    """Construct a game-neutral board from a validated game definition.

    A package owns its initial position and piece capability data. The engine
    does not select a game by name or hardcode any game's piece types.

    Args:
        definition: Configuration returned by `load_definition`.

    Returns:
        Board: Board with exactly the configured dimensions and starting pieces.
    """
    from engine.model.game.board import Board
    from engine.model.pieces.piece import Piece

    rows, cols = definition.board["rows"], definition.board["columns"]
    placements = []
    for entry in definition.board["starting_pieces"]:
        kind = entry["piece"]
        color_name = entry["color"]
        color = 1 if color_name == "white" else -1
        spec = definition.pieces[kind]
        # The supplied vectors are from White's perspective; Black mirrors the row.
        direction = 1 if color_name == "white" else -1
        for position in entry["squares"]:
            def vectors(field: str):
                return [
                    (row * direction if spec.get("color_relative") else row, col)
                    for row, col in spec[field]
                ]

            piece = Piece(
                color,
                kind,
                vectors=vectors("moves"),
                attack_vectors=vectors("attacks"),
                can_jump=spec["jump"],
                repeat=spec["repeat"],
                royal=bool(spec.get("royal", False)),
                name=kind,
            )
            placements.append((tuple(position), piece))
    return Board((rows, cols), placement=placements)


def named_definition(name: str) -> GameDefinition:
    """Look up a validated registered game by name."""
    for definition in installed_definitions():
        if definition.name == name:
            return definition
    raise ConfigurationError(f"unknown installed game {name!r}")
