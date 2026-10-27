"""Validated, data-only game configuration with bounded JSON hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
import re
import json
from typing import Any
from collections.abc import Mapping

from model.game.capture_policy import CapturePolicy
from model.game.schema import (
    MAX_JSON_TEXT_BYTES,
    _bounded_json,
    condition,
    freeze_json,
    thaw_json,
    validate_hooks,
)


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
        starting_side: Opening participant side, integer 1 or -1.
        position_identity: Optional selected state and legal-target repetition policy.
        declared_optional_fields: Frozen parser metadata preserving optional JSON field presence.
        starting_side: Configured initial side, 1 or -1; defaults to 1.
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
    starting_side: int = 1
    position_identity: Mapping[str, Any] | None = None
    draw_offer_timing: str = "any_time"
    draw_agreement_minimum_moves: int = 0

    def __post_init__(self) -> None:
        """Detach and recursively freeze every configuration-owned JSON value.

        Raises:
            ValueError: Nested values are not finite bounded JSON.
        """
        if not self.declared_optional_fields <= {
            "initial_state",
            "halfmove_reset",
            "position_identity",
            "starting_side",
            "draw_offer_timing",
            "draw_agreement_minimum_moves",
        }:
            raise ValueError("unknown declared optional configuration fields")
        if type(
            self.draw_agreement_minimum_moves
        ) is not int or self.draw_agreement_minimum_moves not in (0, 1):
            raise ValueError("draw agreement minimum moves must be zero or one")
        if self.draw_offer_timing not in ("any_time", "after_move"):
            raise ValueError("unknown draw offer timing policy")
        if type(self.starting_side) is not int or self.starting_side not in (-1, 1):
            raise ValueError("starting side must be explicit integer 1 or -1")
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
            "position_identity",
        ):
            object.__setattr__(self, field, freeze_json(getattr(self, field)))


MAX_GAME_JSON_BYTES = MAX_JSON_TEXT_BYTES
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


def load_bundled_definition(name: str) -> GameDefinition:
    """Load one bundled game as inert JSON without importing its Python package.

    Game subdirectories are resource data, not executable plugins. An explicit
    directory selector is never interpreted as a module name or filesystem path.
    """
    if type(name) is not str or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name) is None:
        raise ConfigurationError("game identifier must be a bounded safe directory name")
    try:
        source = resources.files("games").joinpath(name).joinpath("config.json")
        raw_json = source.read_text("utf-8")
    except (ModuleNotFoundError, OSError) as error:
        raise ConfigurationError(f"game {name!r} has no bundled config.json") from error
    return parse_definition_json(raw_json, f"games/{name}")


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
        or not set(data)
        <= TOP_LEVEL_FIELDS
        | {
            "initial_state",
            "halfmove_reset",
            "position_identity",
            "starting_side",
            "draw_offer_timing",
            "draw_agreement_minimum_moves",
        }
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
    minimum_moves = data.get("draw_agreement_minimum_moves", 0)
    if type(minimum_moves) is not int or minimum_moves not in (0, 1):
        raise ConfigurationError("draw agreement minimum moves must be zero or one")
    draw_offer_timing = data.get("draw_offer_timing", "any_time")
    if type(draw_offer_timing) is not str or draw_offer_timing not in ("any_time", "after_move"):
        raise ConfigurationError("draw offer timing must be any_time or after_move")
    starting_side = data.get("starting_side", 1)
    if type(starting_side) is not int or starting_side not in (-1, 1):
        raise ConfigurationError("starting side must be explicit integer 1 or -1")
    position_identity = data.get("position_identity")
    if position_identity is not None:
        try:
            _bounded_json(position_identity)
            if not isinstance(position_identity, dict) or set(position_identity) != {
                "moved_kinds",
                "rule_state",
                "rights",
                "targets",
            }:
                raise ValueError(
                    "position identity requires exact piece, state, rights and target selections"
                )
            selections = {
                "moved_kinds": pieces,
                "rule_state": initial_state["rule_state"],
                "rights": initial_state["special_rights"],
            }
            for field, known in selections.items():
                values = position_identity[field]
                if (
                    not isinstance(values, list)
                    or len(values) > 64
                    or any(not isinstance(value, str) or value not in known for value in values)
                    or len(set(values)) != len(values)
                ):
                    raise ValueError("position identity selects an unknown or duplicate field")
            targets = position_identity["targets"]
            if not isinstance(targets, list) or len(targets) > 32:
                raise ValueError("position targets must be a bounded list")
            names: set[str] = set()
            for target in targets:
                if (
                    not isinstance(target, dict)
                    or set(target) != {"name", "legal_capture"}
                    or not isinstance(target["name"], str)
                    or target["name"] not in initial_state["temporary_targets"]
                    or target["name"] in names
                    or type(target["legal_capture"]) is not bool
                ):
                    raise ValueError(
                        "position target must select one initialized target and eligibility policy"
                    )
                names.add(target["name"])
        except ValueError as error:
            raise ConfigurationError(f"{package}: invalid position identity: {error}") from error
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
        frozenset(
            set(data)
            & {
                "initial_state",
                "halfmove_reset",
                "position_identity",
                "starting_side",
                "draw_offer_timing",
                "draw_agreement_minimum_moves",
            }
        ),
        starting_side,
        freeze_json(position_identity),
        draw_offer_timing,
        minimum_moves,
    )


def board_from_definition(definition: GameDefinition) -> "Board":
    """Construct an independent game-neutral position using validated JSON data.

    Game-specific piece classes are not imported. Every piece is instantiated
    from its declared move/attack geometry, movement rights and symbols. The
    returned board is a distinct mutable projection owned by its caller.
    """
    from model.game.board import Board
    from model.pieces.piece import Piece

    if not isinstance(definition, GameDefinition):
        raise TypeError("a validated game definition is required")
    rows = definition.board["rows"]
    cols = definition.board["columns"]
    placements: list[tuple[tuple[int, int], Piece]] = []
    for record in definition.board["starting_pieces"]:
        color = 1 if record["color"] == "white" else -1
        kind = record["piece"]
        spec = definition.pieces[kind]

        def vectors(field: str) -> list[tuple[int, int]]:
            return [
                (row * color if spec.get("color_relative") else row, col)
                for row, col in spec.get(field, ())
            ]

        symbols = spec["symbols"]
        for square in record["squares"]:
            piece = Piece(
                color=color,
                piece_type=kind,
                vectors=vectors("moves"),
                initial_vectors=vectors("initial_moves"),
                attack_vectors=vectors("attacks"),
                can_jump=spec["jump"],
                max_steps=None if spec["repeat"] else 1,
                name=kind,
                symbols=(symbols["white"], symbols["black"]),
                has_moved=False,
            )
            placements.append(((square[0], square[1]), piece))
    return Board((rows, cols), placement=placements)
