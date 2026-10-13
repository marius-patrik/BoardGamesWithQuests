"""Validated, data-only game configuration with bounded JSON hooks."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from importlib.metadata import entry_points
import json
from typing import Any

from engine.model.game.board import Board
from engine.model.pieces.piece import Piece
from engine.model.game.schema import validate_hooks

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
    rules: tuple[dict[str, Any], ...]
    quests: tuple[dict[str, Any], ...]


MAX_GAME_JSON_BYTES = 262144
TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "name",
        "title",
        "default",
        "playable",
        "board",
        "pieces",
        "clock",
        "exports",
        "appearance",
        "rules",
        "quests",
    }
)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate keys rather than silently overriding validated fields."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def parse_definition_json(raw_json: str, package: str = "<custom>") -> GameDefinition:
    """Validate an untrusted data-only game definition, without dynamic imports."""
    if not isinstance(raw_json, str):
        raise ConfigurationError("configuration must be a JSON document")
    if len(raw_json.encode("utf-8")) > MAX_GAME_JSON_BYTES:
        raise ConfigurationError("configuration exceeds maximum JSON byte size")
    try:
        data = json.loads(
            raw_json,
            object_pairs_hook=_unique_json_object,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ValueError(f"invalid JSON numeric constant: {constant}")
            ),
        )
    except (ValueError, UnicodeError) as error:
        raise ConfigurationError(f"{package}: invalid JSON: {error}") from error
    return validate_definition(data, package)


def load_definition(package: str) -> GameDefinition:
    """Load trusted built-in package JSON, using the same validator as user data."""
    try:
        raw_json = resources.files(package).joinpath("config.json").read_text("utf-8")
    except (ModuleNotFoundError, OSError) as error:
        raise ConfigurationError(f"{package}: missing config.json: {error}") from error
    return parse_definition_json(raw_json, package)


def validate_definition(data: Any, package: str = "<custom>") -> GameDefinition:
    """Validate typed JSON data against one versioned game-neutral contract."""
    if not isinstance(data, dict) or set(data) != TOP_LEVEL_FIELDS:
        raise ConfigurationError(f"{package}: missing or unknown top-level fields")
    if type(data["schema_version"]) is not int:
        raise ConfigurationError(f"{package}: schema version must be an integer")
    if not isinstance(data, dict) or data.get("schema_version") != 2:
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
        if "color_relative" in piece and type(piece["color_relative"]) is not bool:
            raise ConfigurationError(f"{package}: {key}.color_relative must be a boolean")
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
    try:
        validate_hooks(data.get("rules"), data.get("quests"))
    except ValueError as error:
        raise ConfigurationError(f"{package}: invalid declarative behavior: {error}") from error
    if data["playable"] and not data["rules"]:
        raise ConfigurationError(f"{package}: playable game must declare rules")
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
        tuple(data["rules"]),
        tuple(data["quests"]),
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


def board_from_definition(definition: GameDefinition) -> Board:
    """Construct a game-neutral board from a validated game definition.

    A package owns its initial position and piece capability data. The engine
    does not select a game by name or hardcode any game's piece types.

    Args:
        definition: Configuration returned by `load_definition`.

    Returns:
        Board: Board with exactly the configured dimensions and starting pieces.
    """
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
