"""Exercise game JSON input validation and resulting board behavior."""

import copy
import json
from pathlib import Path

import pytest

from engine.model.game.configuration import (
    ConfigurationError,
    board_from_definition,
    load_definition,
    parse_definition_json,
)

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("chess", 8, 8, 32),
    ("english_draughts", 8, 8, 24),
    ("international_checkers", 10, 10, 40),
)


def chess_config() -> dict:
    return json.loads((ROOT / "packages/chess/config.json").read_text("utf-8"))


@pytest.mark.parametrize("game,rows,cols,count", CASES)
def test_shipped_json_creates_expected_piece_placement(
    game: str, rows: int, cols: int, count: int
) -> None:
    definition = load_definition(game)
    board = board_from_definition(definition)
    assert (board.rows, board.cols) == (rows, cols)
    assert definition.playable is False
    assert sum(
        board.get_piece_at((row, col)) is not None
        for row in range(rows) for col in range(cols)
    ) == count


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", True),
        ("schema_version", 200),
        ("playable", "true"),
        ("clock", {"initial_seconds": -1, "increment_seconds": 0}),
        ("clock", {"initial_seconds": True, "increment_seconds": 0}),
        ("rules", [
            {"id": "inject", "hook": "on_move_made", "when": {"op": "true"},
             "effects": [{"op": "__import__", "params": {}}]}
        ]),
    ],
)
def test_untrusted_values_are_rejected_without_affecting_game(
    field: str, value: object
) -> None:
    config = chess_config()
    config[field] = value
    with pytest.raises(ConfigurationError):
        parse_definition_json(json.dumps(config))
    assert load_definition("chess").playable is False


def test_duplicate_piece_coordinates_fail_before_board_creation() -> None:
    config = chess_config()
    config["board"]["starting_pieces"][1]["squares"].append(
        copy.deepcopy(config["board"]["starting_pieces"][0]["squares"][0])
    )
    with pytest.raises(ConfigurationError, match="duplicate square"):
        parse_definition_json(json.dumps(config))


@pytest.mark.parametrize(
    "raw", [
        "null",
        '{"schema_version":2,"schema_version":2}',
        '{"schema_version":NaN}',
        " " * 262145,
    ],
)
def test_unambiguous_bounded_json_is_required(raw: str) -> None:
    with pytest.raises(ConfigurationError):
        parse_definition_json(raw)


def test_executable_extension_and_invalid_capture_policy_fail_closed() -> None:
    config = chess_config()
    config["python_rules"] = "import os"
    with pytest.raises(ConfigurationError):
        parse_definition_json(json.dumps(config))
    config.pop("python_rules")
    config["pieces"]["pawn"]["capture_policy"] = {"flying": "yes"}
    with pytest.raises(ConfigurationError):
        parse_definition_json(json.dumps(config))
