"""Executable G1 primitive expressiveness probes, not complete game-rule tests.

All cases use actual generic board geometry, snapshot history and hook evaluation.
The subsequent G2/G3 gates will compose these primitives into full rulebooks.
"""

from engine.model.game.board import Board
from engine.model.game.board_queries import BoardQueries
from engine.model.game.capture_geometry import CaptureEnumerator, CapturePolicy
from engine.model.game.configuration import load_definition
from engine.model.game.hooks import HookInterpreter
from engine.model.game.snapshot_queries import SnapshotQueries
from engine.model.pieces.piece import Piece


def piece(side: int, kind: str, *, flying: bool = False) -> Piece:
    """Construct an unbranded piece with diagonal capture capabilities."""
    diagonal = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return Piece(side, kind, vectors=diagonal, attack_vectors=diagonal, repeat=flying)


def rule(name: str, hook: str, condition: dict, effect: str) -> dict:
    """Build one validated JSON-style rule with a generic effect."""
    return {
        "id": name,
        "hook": hook,
        "when": condition,
        "effects": [{"op": effect, "params": {}}],
    }


def call(rules: list[dict], bindings: dict, hook: str) -> list[str]:
    """Evaluate a real condition against trusted generic query primitives."""
    return [effect.op for effect in HookInterpreter(rules, bindings).evaluate(hook).effects]


def comparison(name: str, relation: str, value: object) -> dict:
    """Compare one game-neutral snapshot field with a typed literal."""
    return {
        "op": "compare",
        "relation": relation,
        "left": {"query": "move_attribute", "params": {"name": name}},
        "right": value,
    }


# English draughts: a man can make a compulsory two-hop capture sequence.
man = piece(1, "man")
enemy = piece(-1, "man")
english = Board((8, 8), [((5, 2), man), ((4, 3), enemy), ((2, 5), enemy)])
english_def = load_definition("english_draughts")
short = CapturePolicy.from_json(english_def.pieces["man"]["capture_policy"])
english_paths = CaptureEnumerator(english).enumerate((5, 2), short)
assert english_paths and max(len(path["steps"]) for path in english_paths) == 2
assert english.get_piece_at((5, 2)) is man
assert english.get_piece_at((4, 3)) is enemy
short_moves = english_paths[0]["steps"]
assert short_moves[0]["landing"] == [3, 4]
assert short_moves[1]["landing"] == [1, 6]
english_data = {
    "capture_paths": english_paths,
    "move_attributes": {"captures": 0, "distance": 1},
}
capture_rule = rule(
    "must_capture",
    "permits_move",
    {
        "op": "all",
        "args": [
            {"op": "test", "query": "capture_paths", "params": {"side": "active"}},
            comparison("captures", "eq", 0),
        ],
    },
    "deny",
)
assert call([capture_rule], SnapshotQueries(english_data).bindings(), "permits_move") == ["deny"]
english_data["move_attributes"]["captures"] = 2
assert call([capture_rule], SnapshotQueries(english_data).bindings(), "permits_move") == []
# Single-step (short) king capture never offers a square beyond adjacent landing.
king_short = Board((8, 8), [((5, 2), piece(1, "king")), ((4, 3), enemy)])
king_paths = CaptureEnumerator(king_short).enumerate(
    (5, 2), CapturePolicy.from_json(english_def.pieces["king"]["capture_policy"])
)
assert {tuple(step["landing"]) for path in king_paths for step in path["steps"]} == {(3, 4)}

# International draughts: flying king and backward man capture.
international_def = load_definition("international_checkers")
flying = CapturePolicy.from_json(
    international_def.pieces["king"]["capture_policy"]
)
international = Board(
    (10, 10),
    [
        ((7, 0), piece(1, "king", flying=True)),
        ((5, 2), enemy),
        ((2, 5), enemy),
    ],
)
international_paths = CaptureEnumerator(international).enumerate((7, 0), flying)
assert international_paths
assert max(len(path["steps"]) for path in international_paths) == 2
assert any(
    path["steps"][0]["landing"] == [4, 3] and len(path["steps"]) == 2
    for path in international_paths
)
reverse = Board((10, 10), [((3, 4), piece(1, "man")), ((4, 5), enemy)])
assert any(
    path["steps"][0]["landing"] == [5, 6]
    for path in CaptureEnumerator(reverse).enumerate(
        (3, 4), CapturePolicy.from_json(international_def.pieces["man"]["capture_policy"])
    )
)
maximal = {
    "capture_paths": international_paths,
    "move_attributes": {"captures": 1},
}
max_rule = rule(
    "maximum_capture",
    "permits_move",
    {
        "op": "compare",
        "relation": "eq",
        "left": {"query": "capture_count", "params": {"scope": "candidate"}},
        "right": {"query": "capture_count", "params": {"scope": "maximum"}},
    },
    "permit",
)
assert call([max_rule], SnapshotQueries(maximal).bindings(), "permits_move") == []
maximal["move_attributes"]["captures"] = 2
assert call([max_rule], SnapshotQueries(maximal).bindings(), "permits_move") == ["permit"]

# Chess: position history, rights, attacked transit squares, en passant and
# promotion are generic metadata/geometry rather than chess engine branches.
chess = Board(
    (8, 8),
    [
        ((7, 4), piece(1, "royal")),
        ((7, 7), piece(1, "tower")),
        ((0, 5), piece(-1, "tower")),
    ],
)
# Use an orthogonal attack vector for the opposing long-range tower.
attacker = Piece(-1, "tower", vectors=[(1, 0)], attack_vectors=[(1, 0)], repeat=True)
chess.set_piece_at((0, 5), attacker)
facts = BoardQueries(chess, 1)
assert facts.squares_attacked({"target": [7, 5], "by_side": "opponent"})
chess.set_piece_at((0, 5), None)
assert not facts.squares_attacked({"target": [7, 5], "by_side": "opponent"})

metadata = {
    "special_rights": {"active_royal_short": True},
    "temporary_targets": {"en_passant": [2, 3]},
    "promotion_options": {"active": ["queen", "rook", "bishop", "knight"]},
    "position_key": "canonical-position-hash",
    "position_history": ["canonical-position-hash"] * 3,
    "move_attributes": {"captures": 0},
}
snap = SnapshotQueries(metadata)
castle = rule(
    "castling_rights",
    "permits_move",
    {
        "op": "test",
        "query": "special_rights",
        "params": {"name": "active_royal_short"},
    },
    "permit",
)
assert call([castle], snap.bindings(), "permits_move") == ["permit"]
ep = rule(
    "en_passant",
    "permits_move",
    {
        "op": "compare",
        "relation": "eq",
        "left": {"query": "temporary_target", "params": {"name": "en_passant"}},
        "right": [2, 3],
    },
    "permit",
)
assert call([ep], snap.bindings(), "permits_move") == ["permit"]
promotion = rule(
    "promotion",
    "on_move_made",
    {
        "op": "compare",
        "relation": "in",
        "left": "queen",
        "right": {"query": "promotion_options", "params": {"side": "active"}},
    },
    "replace_piece",
)
assert call([promotion], snap.bindings(), "on_move_made") == ["replace_piece"]
draw = rule(
    "threefold",
    "outcome",
    {
        "op": "compare",
        "relation": "gte",
        "left": {"query": "repetition_count", "params": {"scope": "position"}},
        "right": 3,
    },
    "propose_outcome",
)
assert call([draw], snap.bindings(), "outcome") == ["propose_outcome"]
assert snap.repetition_count({"scope": "position"}) == 3

# Dynamic references resolve solely against a trusted, typed current move.
from engine.model.game.schema import validate_hooks

move_refs = {"move.start": [7, 4], "move.end": [7, 6]}
move_rule = rule(
    "generic_move",
    "on_move_made",
    {
        "op": "compare",
        "relation": "eq",
        "left": {"ref": "move.start"},
        "right": [7, 4],
    },
    "move_piece",
)
move_rule["effects"][0]["params"] = {
    "start": {"ref": "move.start"},
    "end": {"ref": "move.end"},
}
planned = HookInterpreter([move_rule], {}, move_refs).evaluate("on_move_made")
assert planned.matched_rule_ids == ("generic_move",)
assert dict(planned.effects[0].params) == {"start": [7, 4], "end": [7, 6]}
assert move_refs == {"move.start": [7, 4], "move.end": [7, 6]}
for invalid in (
    {"ref": "__globals__.builtins"},
    {"ref": "move.__class__"},
    {"ref": "game.private._secret"},
):
    malformed = rule(
        "bad_reference",
        "permits_move",
        {"op": "compare", "relation": "eq", "left": invalid, "right": 1},
        "permit",
    )
    try:
        validate_hooks([malformed], [])
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe reference accepted")

print("G1 generic capture, temporal, geometry and declarative hook probes passed")
