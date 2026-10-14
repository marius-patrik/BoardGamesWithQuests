"""Validated, data-only game configuration with bounded JSON hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from importlib.metadata import entry_points
import json
from typing import Any
from collections.abc import Mapping

from engine.model.game.board import Board
from engine.model.game.capture_geometry import CapturePolicy
from engine.model.pieces.piece import Piece
from engine.model.game.schema import (
    _bounded_json,
    condition,
    freeze_json,
    thaw_json,
    validate_hooks,
)

GROUP = "boardgameswithquests.games"


class ConfigurationError(ValueError):
    """The installed game's declarative settings are invalid."""


@dataclass(frozen=True)
class GameDefinition:
    """Immutable configuration snapshot owned by one selected game.

    Args:
        name: Configuration identity.
        package: Trusted installed package or custom-source identifier.
        title: Display name.
        default: Whether the catalog preselects this definition.
        playable: Whether its complete rulebook is verified.
        board: Dimensions and starting placements.
        pieces: Declared movement and appearance capabilities.
        clock: Explicit time controls.
        exports: Trusted game-owned format declarations.
        appearance: Board colors.
        rules: Declarative hook definitions.
        quests: Declarative quest definitions.
        initial_state: Immutable initial rule values, rights and temporary targets.
        halfmove_reset: Optional additional reset condition evaluated on original state.
        declared_optional_fields: Frozen parser metadata preserving optional JSON field presence.
    """

    name: str
    package: str
    title: str
    default: bool
    playable: bool
    board: Mapping[str, Any]
    pieces: Mapping[str, Mapping[str, Any]]
    clock: Mapping[str, Any]
    exports: tuple[str, ...]
    appearance: Mapping[str, Any]
    rules: tuple[Mapping[str, Any], ...]
    quests: tuple[Mapping[str, Any], ...]
    initial_state: Mapping[str, Any] = field(
        default_factory=lambda: {
            "rule_state": {},
            "special_rights": {},
            "temporary_targets": {},
        }
    )
    halfmove_reset: Mapping[str, Any] | None = None
    declared_optional_fields: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Detach and recursively freeze every configuration-owned JSON value.

        Raises:
            ValueError: Nested values are not finite bounded JSON.
        """
        if not self.declared_optional_fields <= {"initial_state", "halfmove_reset"}:
            raise ValueError("unknown declared optional configuration fields")
        object.__setattr__(
            self, "declared_optional_fields", frozenset(self.declared_optional_fields)
        )
        for field in (
            "board",
            "pieces",
            "clock",
            "appearance",
            "rules",
            "quests",
            "exports",
            "initial_state",
            "halfmove_reset",
        ):
            object.__setattr__(self, field, freeze_json(getattr(self, field)))


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
    """Validate an untrusted data-only game definition without dynamic imports.

    Args:
        raw_json: Untrusted UTF-8-compatible JSON document.
        package: Source identifier used in validation errors.

    Returns:
        Detached immutable validated configuration.

    Raises:
        ConfigurationError: Text, fields, types or complexity are invalid.
    """
    if not isinstance(raw_json, str):
        raise ConfigurationError("configuration must be a JSON document")
    try:
        if len(raw_json.encode("utf-8")) > MAX_GAME_JSON_BYTES:
            raise ConfigurationError("configuration exceeds maximum JSON byte size")
        data = json.loads(
            raw_json,
            object_pairs_hook=_unique_json_object,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ValueError(f"invalid JSON numeric constant: {constant}")
            ),
        )
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ConfigurationError(f"{package}: invalid JSON: {error}") from error
    try:
        return validate_definition(data, package)
    except (ValueError, TypeError, RecursionError) as error:
        raise ConfigurationError(f"{package}: invalid configuration: {error}") from error


def load_definition(package: str) -> GameDefinition:
    """Load trusted built-in package JSON, using the same validator as user data."""
    try:
        raw_json = resources.files(package).joinpath("config.json").read_text("utf-8")
    except (ModuleNotFoundError, OSError) as error:
        raise ConfigurationError(f"{package}: missing config.json: {error}") from error
    return parse_definition_json(raw_json, package)


def validate_definition(data: Any, package: str = "<custom>") -> GameDefinition:
    """Validate typed JSON data against the closed game-neutral contract.

    Args:
        data: Untrusted decoded JSON object.
        package: Source identifier used in validation errors.

    Returns:
        Detached immutable validated configuration.

    Raises:
        ConfigurationError: Definition fields, values or complexity are invalid.
    """
    if (
        not isinstance(data, dict)
        or not TOP_LEVEL_FIELDS <= set(data)
        or not set(data) <= TOP_LEVEL_FIELDS | {"initial_state", "halfmove_reset"}
    ):
        raise ConfigurationError(f"{package}: missing or unknown top-level fields")
    try:
        encoded = json.dumps(
            data, allow_nan=False, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError, UnicodeError) as error:
        raise ConfigurationError(f"{package}: configuration must be finite UTF-8 JSON") from error
    if len(encoded) > MAX_GAME_JSON_BYTES:
        raise ConfigurationError(f"{package}: configuration exceeds maximum JSON byte size")
    if type(data["schema_version"]) is not int:
        raise ConfigurationError(f"{package}: schema version must be an integer")
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise ConfigurationError(f"{package}: unsupported config schema version")
    try:
        # A document budget differs from the deliberately smaller per-expression budget.
        detached = thaw_json(freeze_json(data))
    except ValueError as error:
        raise ConfigurationError(f"{package}: {error}") from error
    data = detached
    name, title = data.get("name"), data.get("title")
    if not all(isinstance(v, str) and v and len(v) <= 256 for v in (name, title)):
        raise ConfigurationError(f"{package}: name and title must be strings")
    if not all(type(data.get(v)) is bool for v in ("default", "playable")):
        raise ConfigurationError(f"{package}: default and playable must be booleans")
    board = data.get("board")
    if not isinstance(board, dict) or set(board) != {"rows", "columns", "starting_pieces"}:
        raise ConfigurationError(f"{package}: missing board definition")
    rows, cols = board.get("rows"), board.get("columns")
    if not all(type(v) is int and 1 <= v <= 256 for v in (rows, cols)) or rows * cols > 4096:
        raise ConfigurationError(f"{package}: board dimensions are invalid")
    pieces = data.get("pieces")
    if not isinstance(pieces, dict) or not pieces or len(pieces) > 128:
        raise ConfigurationError(f"{package}: pieces must be a nonempty object")
    for key, piece in pieces.items():
        if not isinstance(key, str) or not isinstance(piece, dict):
            raise ConfigurationError(f"{package}: malformed piece")
        required = {"symbols", "moves", "attacks", "jump", "repeat"}
        optional = {
            "color_relative",
            "capture_policy",
            "notation",
            "fen",
            "initial_moves",
            "promotion",
        }
        if not required <= set(piece) or not set(piece) <= required | optional:
            raise ConfigurationError(f"{package}: {key} has missing or unknown fields")
        if not key or len(key) > 128:
            raise ConfigurationError(f"{package}: invalid piece identifier")
        if "notation" in piece and (
            not isinstance(piece["notation"], str) or len(piece["notation"]) > 16
        ):
            raise ConfigurationError(f"{package}: invalid notation symbol")
        if "fen" in piece and (
            not isinstance(piece["fen"], str)
            or len(piece["fen"]) != 1
            or not piece["fen"].isascii()
            or not piece["fen"].isalpha()
        ):
            raise ConfigurationError(f"{package}: FEN symbol must be one ASCII letter")
        symbols = piece.get("symbols")
        if (
            not isinstance(symbols, dict)
            or set(symbols) != {"white", "black"}
            or any(
                not isinstance(symbols.get(color), str)
                or not symbols[color]
                or len(symbols[color]) > 32
                for color in ("white", "black")
            )
        ):
            raise ConfigurationError(f"{package}: {key} needs white and black symbols")
        for kind in ("moves", "attacks", "initial_moves"):
            if kind == "initial_moves" and kind not in piece:
                continue
            vectors = piece.get(kind)
            if (
                not isinstance(vectors, list)
                or not vectors
                or len(vectors) > 32
                or any(
                    not isinstance(v, list)
                    or len(v) != 2
                    or any(type(axis) is not int or abs(axis) > max(rows, cols) for axis in v)
                    or v == [0, 0]
                    for v in vectors
                )
            ):
                raise ConfigurationError(f"{package}: {key}.{kind} has invalid vectors")
        if any(type(piece.get(prop)) is not bool for prop in ("jump", "repeat")):
            raise ConfigurationError(f"{package}: {key} requires jump/repeat booleans")
        if "color_relative" in piece and type(piece["color_relative"]) is not bool:
            raise ConfigurationError(f"{package}: {key}.color_relative must be a boolean")
        if "capture_policy" in piece:
            try:
                CapturePolicy.from_json(piece["capture_policy"])
            except (ValueError, TypeError) as error:
                raise ConfigurationError(
                    f"{package}: {key}.capture_policy is invalid: {error}"
                ) from error
    for key, piece in pieces.items():
        if "promotion" not in piece:
            continue
        promotion = piece["promotion"]
        if (
            not isinstance(promotion, dict)
            or set(promotion) != {"rank", "options", "mode", "stop_capture"}
            or promotion["rank"] != "far"
            or promotion["mode"] not in ("choice", "automatic")
            or type(promotion["stop_capture"]) is not bool
            or not isinstance(promotion["options"], list)
            or not 1 <= len(promotion["options"]) <= 32
            or any(not isinstance(kind, str) or kind not in pieces for kind in promotion["options"])
            or len(set(promotion["options"])) != len(promotion["options"])
            or (promotion["mode"] == "automatic" and len(promotion["options"]) != 1)
        ):
            raise ConfigurationError(f"{package}: {key} has invalid promotion policy")
    placements = board.get("starting_pieces")
    if not isinstance(placements, list):
        raise ConfigurationError(f"{package}: starting_pieces must be a list")
    occupied: set[tuple[int, int]] = set()
    if len(placements) > 128:
        raise ConfigurationError(f"{package}: too many starting piece groups")
    for placement in placements:
        if (
            not isinstance(placement, dict)
            or set(placement) != {"piece", "color", "squares"}
            or not isinstance(placement.get("piece"), str)
            or placement["piece"] not in pieces
        ):
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
            if len(occupied) > 2048:
                raise ConfigurationError(f"{package}: too many starting pieces")
    clock = data.get("clock")
    if (
        not isinstance(clock, dict)
        or set(clock) != {"initial_seconds", "increment_seconds"}
        or any(
            type(clock.get(key)) is not int or not 0 <= clock[key] <= 315360000
            for key in ("initial_seconds", "increment_seconds")
        )
    ):
        raise ConfigurationError(f"{package}: invalid clock")
    exports = data.get("exports", [])
    if (
        not isinstance(exports, list)
        or len(exports) > 32
        or any(not isinstance(v, str) or not v or len(v) > 128 for v in exports)
    ):
        raise ConfigurationError(f"{package}: invalid exports")
    appearance = data.get("appearance", {})
    if (
        not isinstance(appearance, dict)
        or not set(appearance) <= {"light_square", "dark_square"}
        or any(
            not isinstance(value, str)
            or len(value) != 7
            or value[0] != "#"
            or any(char not in "0123456789abcdefABCDEF" for char in value[1:])
            for value in appearance.values()
        )
    ):
        raise ConfigurationError(f"{package}: invalid appearance")
    try:
        validate_hooks(data.get("rules"), data.get("quests"))
    except ValueError as error:
        raise ConfigurationError(f"{package}: invalid declarative behavior: {error}") from error
    if data["playable"] and not data["rules"]:
        raise ConfigurationError(f"{package}: playable game must declare rules")
    initial_state = data.get(
        "initial_state", {"rule_state": {}, "special_rights": {}, "temporary_targets": {}}
    )
    if not isinstance(initial_state, dict) or set(initial_state) != {
        "rule_state",
        "special_rights",
        "temporary_targets",
    }:
        raise ConfigurationError("initial state requires rule state, rights and temporary targets")
    try:
        _bounded_json(initial_state)
        if any(not isinstance(value, dict) for value in initial_state.values()):
            raise ValueError("initial state fields must be objects")
        if any(not name or len(name) > 128 for values in initial_state.values() for name in values):
            raise ValueError("initial state keys must be bounded nonempty strings")
        if any(type(value) is not bool for value in initial_state["special_rights"].values()):
            raise ValueError("initial rights must be booleans")
        for square in initial_state["temporary_targets"].values():
            if square is not None and (
                not isinstance(square, list)
                or len(square) != 2
                or any(type(axis) is not int for axis in square)
                or not (0 <= square[0] < rows and 0 <= square[1] < cols)
            ):
                raise ValueError("initial temporary target must be an in-bounds square or null")
        halfmove_reset = data.get("halfmove_reset")
        if halfmove_reset is not None:
            condition(halfmove_reset)
    except ValueError as error:
        raise ConfigurationError(f"{package}: invalid initial lifecycle policy: {error}") from error
    return GameDefinition(
        name,
        package,
        title,
        data["default"],
        data["playable"],
        freeze_json(board),
        freeze_json(pieces),
        freeze_json(clock),
        tuple(exports),
        freeze_json(appearance),
        freeze_json(data["rules"]),
        freeze_json(data["quests"]),
        freeze_json(initial_state),
        freeze_json(halfmove_reset),
        frozenset(set(data) & {"initial_state", "halfmove_reset"}),
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

            def vectors(field: str) -> list[tuple[int, int]]:
                """Resolve the configured vectors relative to the piece side.

                Args:
                    field: Validated piece vector field.

                Returns:
                    Side-relative movement offsets.
                """
                return [
                    (row * direction if spec.get("color_relative") else row, col)
                    for row, col in spec[field]
                ]

            piece = Piece(
                color,
                kind,
                vectors=vectors("moves"),
                initial_vectors=vectors("initial_moves") if "initial_moves" in spec else [],
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
