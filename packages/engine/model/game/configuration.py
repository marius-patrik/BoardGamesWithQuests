<<<<<<< HEAD:packages/engine/model/game/configuration.py
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
    MAX_JSON_TEXT_BYTES,
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
        }:
            raise ValueError("unknown declared optional configuration fields")
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
        or not set(data)
        <= TOP_LEVEL_FIELDS
        | {"initial_state", "halfmove_reset", "position_identity", "starting_side"}
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
            set(data) & {"initial_state", "halfmove_reset", "position_identity", "starting_side"}
        ),
        starting_side,
        freeze_json(position_identity),
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
||||||| b45d2e0f:packages/engine/model/game/configuration.py
=======
"""Loading a configuration.

A configuration is a directory under `games/`, and it is composed explicitly: the
configuration's own module says what it is made of. There is no registry and no
discovery-by-name, so the set of rules in force is closed, greppable and known at the point
of use.

Loading is bounded on purpose. Code loads from inside the configuration directory being
edited and from nowhere else — never an arbitrary path, never an environment variable —
because the product runs the Python a player writes.
"""

import importlib.util
import json
import os
import re
import shutil
import sys
from typing import Callable, Any, Dict, Iterable, List, Optional

from model.game.board import Board
from model.game.games import DEFAULT_GAME, available_games, games_root
from model.game.quest import Quest
from model.game.rule import Rule

#: Subdirectories a configuration directory holds.
CONFIGURATION_SECTIONS = ("pieces", "rules", "quests", "clocks", "export")


class Configuration:
    """One game, assembled: a board, its pieces, its rules, its quests and its clocks.

    Attributes:
        name: The configuration's directory name.
        path: Absolute path to the configuration directory.
        board: The board the game runs on.
        pieces: The piece classes this configuration offers.
        rules: The rules in force, in the order they are declared.
        quests: The quests available.
        clocks: The clock configurations available.
        exporters: The export writers this configuration offers.
        package: The module name the configuration is registered under, so a module inside it
            can resolve its relative imports. Empty until the configuration is loaded from a
            directory, which is the only way a relative import can work at all.
    """

    def __init__(
        self,
        name: str,
        path: str,
        board: Optional[Board] = None,
        pieces: Optional[Iterable[type]] = None,
        rules: Optional[Iterable[Rule]] = None,
        quests: Optional[Iterable[Quest]] = None,
        clocks: Optional[Iterable[Any]] = None,
        exporters: Optional[Iterable[Any]] = None,
        board_factory: Optional[Callable[[], Board]] = None,
    ):
        """Assemble a configuration.

        Args:
            name: The configuration's directory name.
            path: Absolute path to the configuration directory.
            board: The board the game runs on.
            pieces: The piece classes this configuration offers.
            rules: The rules in force, in the order they are declared.
            quests: The quests available.
            clocks: The clock configurations available.
            exporters: The export writers this configuration offers.
            board_factory: Builds a fresh board for this configuration. Holding one board
                means one game; holding the way to build one means as many games as the
                player has time for.
        """
        self.name = name
        self.path = path
        self.board = board
        self.pieces: List[type] = list(pieces) if pieces else []
        self.rules: List[Rule] = list(rules) if rules else []
        self.quests: List[Quest] = list(quests) if quests else []
        self.clocks: List[Any] = list(clocks) if clocks else []
        self.exporters: List[Any] = list(exporters) if exporters else []
        self.board_factory: Optional[Callable[[], Board]] = board_factory
        self.package: str = ""

    @property
    def is_default(self) -> bool:
        """Whether this is the shipped default configuration, which may not be edited.

        The default configuration is the one a game runs when the player selects nothing, so
        it is the reference every variant is compared against. A variant starts by duplicating
        it, and the default itself is left exactly as shipped — which is only a rule if
        something enforces it, because `save_values` can write into its directory perfectly
        well.

        Returns:
            bool: True for the configuration named by `DEFAULT_GAME`.
        """
        return self.name == DEFAULT_GAME

    def new_board(self) -> Board:
        """Build a fresh board for a new game of this configuration.

        Returns:
            Board: A newly dealt board. A configuration that declared no factory gets the
            board it already holds, so `new_game` always returns a playable board even when
            a configuration declares only one.
        """
        if self.board_factory is not None:
            return self.board_factory()
        if self.board is not None:
            return self.board
        return Board()

    def enabled_rules(self) -> List[Rule]:
        """Return the rules that are in force, in declaration order.

        Returns:
            List[Rule]: The rules whose `enabled` is True.
        """
        return [rule for rule in self.rules if rule.enabled]

    def reset(self) -> None:
        """Clear every rule's runtime state for a new game.

        Returns:
            None
        """
        for rule in self.rules:
            rule.reset()

    def values(self) -> Dict[str, Any]:
        """Return everything about this configuration that may be written to disk.

        Returns:
            Dict[str, Any]: The name, the board dimensions and every rule's and quest's
            configured values. No rule's runtime state is here, so saving a configuration
            cannot save a game's history.
        """
        return {
            "name": self.name,
            "board": list(self.board.dimensions) if self.board is not None else None,
            "rules": {rule.label: rule.persisted_values() for rule in self.rules},
            "quests": {
                quest.name: {"reward": quest.reward, "enabled": quest.enabled}
                for quest in self.quests
            },
        }

    def save_values(self, path: Optional[str] = None) -> str:
        """Write the configurable values to disk as JSON.

        Only values are written. Runtime state is not part of `values()`, so it cannot
        reach the file even by accident.

        The default configuration is not written to. It is the reference a variant is
        duplicated from, so editing it in place destroys the one thing every variant is
        compared against, and no warning is given. Writing it *outside* its own directory
        is fine: that is an export, not an edit.

        Args:
            path: Where to write. Defaults to `<configuration path>/configuration.json`.

        Returns:
            str: The path written.

        Raises:
            PermissionError: If the target is inside the default configuration's directory.
        """
        target = path or os.path.join(self.path, "configuration.json")
        if self.is_default and _within(os.path.abspath(target), os.path.abspath(self.path)):
            raise PermissionError(
                f"{self.name} is the default configuration and cannot be edited; "
                f"duplicate it into a variant and edit that instead"
            )
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(self.values(), handle, indent=2, sort_keys=True, default=str)
        return target

    def __repr__(self) -> str:
        """Return a debugging representation naming the configuration.

        Returns:
            str: The name, its path, and how many rules and quests it holds.
        """
        return (
            f"Configuration(name={self.name!r}, path={self.path!r}, "
            f"rules={len(self.rules)}, quests={len(self.quests)})"
        )


def _within(candidate: str, directory: str) -> bool:
    """Report whether a path lies inside a directory.

    Args:
        candidate: The path to test. Must already be absolute.
        directory: The containing directory. Must already be absolute.

    Returns:
        bool: True when `candidate` is inside `directory` or is `directory` itself.
    """
    try:
        return os.path.commonpath([candidate, directory]) == directory
    except ValueError:  # pragma: no cover - different drives on Windows
        return False


def _validate_name(name: str) -> str:
    """Check that a name may be used for a configuration directory.

    A name becomes both a directory and the module name a loaded configuration is registered
    under, so it has to be one path segment and an identifier. Anything else is either a
    traversal or a name Python will not accept.

    Args:
        name: The proposed directory name.

    Returns:
        str: The name, unchanged.

    Raises:
        ValueError: If the name is empty, holds a path separator, or is a relative marker.
    """
    if not name or os.path.sep in name or name in (".", "..") or not name.isidentifier():
        raise ValueError(f"{name!r} is not a configuration name")
    return name


def copy_configuration(source: str, name: str, root: Optional[str] = None) -> Configuration:
    """Duplicate a configuration directory into a new variant, and load the copy.

    Duplication is the extension mechanism: `SCRATCHPAD.md` section 2 makes copying a
    directory how a variant comes into existence, so this is that move with the loading
    done and the copy refused where it would be wrong.

    Args:
        source: The configuration directory name to copy from.
        name: The variant's directory name.
        root: The directory configurations must live under. Defaults to the shipped `games/`.

    Returns:
        Configuration: The loaded copy, which is a variant in its own right.

    Raises:
        ValueError: If `name` is not a usable configuration name.
        FileNotFoundError: If there is no configuration named `source`.
        FileExistsError: If `name` already exists, so nothing is overwritten.
    """
    _validate_name(name)
    if name == DEFAULT_GAME:
        raise ValueError(f"{DEFAULT_GAME} is the default configuration and already exists")
    allowed = os.path.abspath(root or games_root())
    origin = os.path.join(allowed, source)
    if not os.path.isdir(origin):
        raise FileNotFoundError(f"no configuration directory named {source!r} in {allowed}")
    target = os.path.join(allowed, name)
    if os.path.exists(target):
        raise FileExistsError(f"{target} already exists")
    shutil.copytree(origin, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return load_configuration_at(target, root=allowed)


def rename_configuration(name: str, new_name: str, root: Optional[str] = None) -> Configuration:
    """Rename a configuration directory, and load it under its new name.

    Args:
        name: The configuration directory's current name.
        new_name: The name to give it.
        root: The directory configurations must live under. Defaults to the shipped `games/`.

    Returns:
        Configuration: The loaded configuration under its new name.

    Raises:
        ValueError: If `new_name` is not usable, or names the configuration being renamed.
        FileNotFoundError: If there is no configuration named `name`.
        FileExistsError: If `new_name` is already taken.
    """
    _validate_name(new_name)
    if new_name == DEFAULT_GAME:
        raise ValueError(f"{DEFAULT_GAME} is the default configuration and cannot take a name")
    allowed = os.path.abspath(root or games_root())
    origin = os.path.join(allowed, name)
    if not os.path.isdir(origin):
        raise FileNotFoundError(f"no configuration directory named {name!r} in {allowed}")
    if name == DEFAULT_GAME:
        raise PermissionError(f"{DEFAULT_GAME} is the default configuration and cannot be renamed")
    if new_name == name:
        return load_configuration(name, root=allowed)
    target = os.path.join(allowed, new_name)
    if os.path.exists(target):
        raise FileExistsError(f"{target} already exists")
    os.rename(origin, target)
    return load_configuration_at(target, root=allowed)


def delete_configuration(name: str, root: Optional[str] = None) -> None:
    """Delete a configuration directory.

    Args:
        name: The configuration directory to remove.
        root: The directory configurations must live under. Defaults to the shipped `games/`.

    Returns:
        None

    Raises:
        PermissionError: If asked to delete the default configuration.
        FileNotFoundError: If there is no configuration named `name`.
    """
    allowed = os.path.abspath(root or games_root())
    if name == DEFAULT_GAME:
        raise PermissionError(f"{DEFAULT_GAME} is the default configuration and cannot be deleted")
    target = os.path.join(allowed, name)
    if not os.path.isdir(target):
        raise FileNotFoundError(f"no configuration directory named {name!r} in {allowed}")
    shutil.rmtree(target)


def load_configuration_at(path: str, root: Optional[str] = None) -> Configuration:
    """Load a configuration from a directory path.

    Args:
        path: Absolute path to the configuration directory.
        root: The directory configurations must live under. Defaults to the shipped
            `games/` directory.

    Returns:
        Configuration: The assembled configuration.

    Raises:
        ValueError: If `path` is not inside `root`. Loading player-authored code from an
            arbitrary path is exactly what the bound is for.
        FileNotFoundError: If `path` is not a directory, or holds no `build_configuration`.
    """
    allowed = os.path.abspath(root or games_root())
    resolved = os.path.abspath(path)
    if os.path.commonpath([allowed, resolved]) != allowed:
        raise ValueError(f"a configuration must live under {allowed}; {resolved} is outside it")
    if not os.path.isdir(resolved):
        raise FileNotFoundError(f"no configuration directory at {resolved}")

    name = os.path.basename(resolved)
    entry_point = os.path.join(resolved, "__init__.py")
    if not os.path.isfile(entry_point):
        raise FileNotFoundError(f"{resolved} holds no __init__.py, so it is not a configuration")

    module = _import_from_path(entry_point, resolved)
    builder = getattr(module, "build_configuration", None)
    if builder is None:
        raise FileNotFoundError(f"{resolved} declares no build_configuration()")

    configuration = builder()
    configuration.name = name
    configuration.path = resolved
    configuration.package = module.__name__
    return configuration


def _import_from_path(entry_point: str, directory: str) -> Any:
    """Import a configuration's `__init__.py` as a package rooted where it lives.

    Loading by file location rather than by package name is what lets a player create a
    variant called whatever they like: the name is a directory, not an identifier the
    engine has to agree with.

    The module is registered as a *package* — its spec carries the configuration directory
    as its search path — because that is what makes `from .board import build_board` resolve
    against the copy that wrote it. Without the search path a relative import fails outright,
    and the tempting repair is an absolute `from games.chess.board import …`, which loads the
    original configuration while the copy looks like it loaded its own. So a variant gets its
    own modules here, and nothing in it needs to know what the original is called.

    Args:
        entry_point: Absolute path to the configuration's `__init__.py`.
        directory: The configuration directory, used to give the module a stable unique name.

    Returns:
        Any: The imported module.

    Raises:
        ImportError: If the module cannot be loaded.
    """
    module_name = "_configuration_" + re.sub(r"\W", "_", os.path.abspath(directory))
    spec = importlib.util.spec_from_file_location(
        module_name, entry_point, submodule_search_locations=[directory]
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load a configuration from {entry_point}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def load_configuration(name: str, root: Optional[str] = None) -> Configuration:
    """Load a shipped configuration by name.

    Args:
        name: The configuration directory name, for example `chess`.
        root: The directory configurations must live under. Defaults to the shipped
            `games/` directory.

    Returns:
        Configuration: The assembled configuration.

    Raises:
        ValueError: If `name` is empty or names something outside the directory.
        FileNotFoundError: If no such configuration is shipped.
    """
    _validate_name(name)
    allowed = os.path.abspath(root or games_root())
    return load_configuration_at(os.path.join(allowed, name), root=allowed)


def load_default_configuration(root: Optional[str] = None) -> Configuration:
    """Load the configuration a game runs when the player selects nothing.

    Args:
        root: The directory configurations must live under. Defaults to the shipped
            `games/` directory.

    Returns:
        Configuration: The assembled configuration.

    Raises:
        FileNotFoundError: If no configuration is shipped at all.
    """
    shipped = available_games()
    if not shipped:
        raise FileNotFoundError(f"no configurations are shipped in {root or games_root()}")
    return load_configuration(shipped[0], root=root)
>>>>>>> fix/independent-review-findings:src/model/game/configuration.py
