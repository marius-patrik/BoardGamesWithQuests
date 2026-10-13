"""Exercise closed immutable JSON definitions and effect contracts (FR-12/34/68/69)."""

import json
from pathlib import Path

import pytest

from engine.model.game.configuration import (
    ConfigurationError,
    board_from_definition,
    parse_definition_json,
    validate_definition,
)
from engine.model.game.hooks import HookInterpreter, PlannedEffect
from engine.model.game.schema import freeze_json, thaw_json, validate_effect
from engine.model.game.validator import MoveValidator


def configuration() -> dict:
    """Return an independent shipped definition for untrusted editor tests."""
    return json.loads((Path(__file__).parents[1] / "packages/chess/config.json").read_text())


def test_editor_mutation_cannot_change_validated_session_board() -> None:
    source = configuration()
    definition = validate_definition(source)
    source["board"]["starting_pieces"][0]["squares"][0][0] = 6
    source["pieces"]["rook"]["moves"][0][0] = 99
    with pytest.raises(TypeError):
        definition.board["rows"] = 12
    with pytest.raises(TypeError):
        definition.pieces["rook"]["moves"][0][0] = 12
    board = board_from_definition(definition)
    assert board.get_piece_at((0, 0)).getType() == "rook"
    assert board.rows == 8
    exported = thaw_json(definition.board)
    exported["rows"] = 12
    assert definition.board["rows"] == 8


def test_initial_vectors_drive_real_relative_candidates() -> None:
    source = configuration()
    source["pieces"]["pawn"]["initial_moves"] = [[-2, 0]]
    board = board_from_definition(validate_definition(source))
    moves = MoveValidator(board)
    assert (4, 4) in moves.get_geometric_moves((6, 4))
    assert (3, 4) in moves.get_geometric_moves((1, 4))
    board.move_piece((6, 4), (5, 4))
    assert (3, 4) not in moves.get_geometric_moves((5, 4))


@pytest.mark.parametrize(
    "path,value",
    [
        (("pieces", "pawn", "python_code"), "exec(unsafe)"),
        (("pieces", "pawn", "fen"), ["p"]),
        (("pieces", "pawn", "initial_moves"), [[True, 0]]),
        (("pieces", "pawn", "symbols", "source"), "unsafe"),
        (("board", "extra"), True),
        (("clock", "tick_function"), "unsafe"),
        (("appearance", "script"), "unsafe"),
        (("appearance", "light_square"), "red"),
    ],
)
def test_nested_invalid_editor_data_cannot_replace_valid_definition(
    path: tuple, value: object
) -> None:
    source = configuration()
    parent = source
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ConfigurationError):
        parse_definition_json(json.dumps(source))
    assert (
        board_from_definition(validate_definition(configuration())).get_piece_at((6, 0)) is not None
    )


@pytest.mark.parametrize("raw", ["\ud800", "[" * 1500 + "0" + "]" * 1500])
def test_hostile_text_has_specific_safe_configuration_error(raw: str) -> None:
    with pytest.raises(ConfigurationError):
        parse_definition_json(raw)


def test_nested_effect_data_remains_immutable_and_serializable() -> None:
    source = {"name": "chain", "value": {"landings": [[3, 4]], "enabled": True}}
    effect = PlannedEffect("set_state", source)
    source["value"]["landings"][0][0] = 0
    with pytest.raises(TypeError):
        effect.params["value"]["landings"][0][0] = 0
    writable = thaw_json(effect.params)
    assert writable["value"]["landings"] == [[3, 4]]
    assert json.loads(json.dumps(writable)) == writable


@pytest.mark.parametrize(
    "op,params",
    [
        ("permit", {}),
        ("deny", {"reason": "capture_required"}),
        ("move_piece", {"start": [0, 0], "end": [0, 1]}),
        ("offer_move", {"start": [0, 0], "end": [0, 1]}),
        ("capture_piece", {"square": [0, 1]}),
        ("replace_piece", {"square": [0, 1], "kind": "promoted"}),
        ("set_state", {"name": "counter", "value": {"count": 1}}),
        ("increment_state", {"name": "counter", "amount": 1}),
        ("record_event", {"name": "captured", "payload": {"square": [0, 1]}}),
        ("propose_outcome", {"kind": "win", "cause": "immobilized", "winner": 1, "priority": 5}),
        ("complete_quest", {"quest": "capture", "player": "alice"}),
        ("set_clock", {"player": -1, "seconds": 0}),
        ("set_rights", {"name": "castle", "value": False}),
    ],
)
def test_valid_effects_produce_detached_observable_plans(op: str, params: dict) -> None:
    rule = {
        "id": "action",
        "hook": "on_move_made",
        "when": {"op": "true"},
        "effects": [{"op": op, "params": params}],
    }
    result = HookInterpreter([rule], {}).evaluate("on_move_made")
    assert result.matched_rule_ids == ("action",)
    assert thaw_json(result.effects[0].params) == params


@pytest.mark.parametrize(
    "op,params",
    [
        ("move_piece", {}),
        ("move_piece", {"start": [True, 0], "end": [0, 1]}),
        ("capture_piece", {"square": [-1, 0]}),
        ("replace_piece", {"square": [0, 1], "kind": ""}),
        ("increment_state", {"name": "counter", "amount": True}),
        ("set_clock", {"player": "alice", "seconds": -1}),
        ("set_rights", {"name": "castle", "value": "true"}),
        ("record_event", {"name": "action", "payload": []}),
        ("propose_outcome", {"kind": "win", "cause": "end", "winner": True, "priority": 0}),
    ],
)
def test_malformed_effects_never_produce_an_executable_plan(op: str, params: dict) -> None:
    with pytest.raises(ValueError):
        PlannedEffect(op, params)


def test_dynamic_reference_is_revalidated_before_effect_emission() -> None:
    rule = {
        "id": "action",
        "hook": "on_move_made",
        "when": {"op": "true"},
        "effects": [
            {"op": "move_piece", "params": {"start": {"ref": "move.start"}, "end": [0, 1]}}
        ],
    }
    with pytest.raises(ValueError):
        HookInterpreter([rule], {}, {"move.start": [True, 0]}).evaluate("on_move_made")
    result = HookInterpreter([rule], {}, {"move.start": [0, 0]}).evaluate("on_move_made")
    assert thaw_json(result.effects[0].params) == {"start": [0, 0], "end": [0, 1]}


def test_immutable_roundtrip_preserves_all_shipped_definition_data() -> None:
    source = configuration()
    assert thaw_json(freeze_json(source)) == source
    assert len(json.dumps(thaw_json(freeze_json(source)))) > 256


def test_decoded_definition_cannot_bypass_document_byte_limit() -> None:
    source = configuration()
    source["quests"] = [
        {"id": "large", "description": "x" * 300000, "when": {"op": "true"}, "reward": 0}
    ]
    with pytest.raises(ConfigurationError, match="byte size"):
        validate_definition(source)
    assert board_from_definition(validate_definition(configuration())).rows == 8


def test_escaped_unpaired_surrogate_is_rejected_after_decoding() -> None:
    source = configuration()
    source["title"] = "\ud800"
    with pytest.raises(ConfigurationError):
        parse_definition_json(json.dumps(source))
