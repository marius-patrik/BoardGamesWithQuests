"""Supplemental checked-in JSON board-creation contract (not GUI acceptance)."""

from __future__ import annotations

from model.game.definition import board_from_definition, load_bundled_definition


def test_chess_starting_state_is_constructed_from_json_not_chess_classes():
    definition = load_bundled_definition("chess")
    position = board_from_definition(definition)
    assert position.rows == position.cols == 8
    placements = [position.get_piece_at((r, c)) for r in range(8) for c in range(8)]
    assert len([piece for piece in placements if piece is not None]) == 32
    rook = position.get_piece_at((7, 0))
    assert rook.getType() == "rook"
    assert rook.getColor() == 1
    assert rook.getMaxSteps() is None
    pawn = position.get_piece_at((6, 0))
    assert pawn.getType() == "pawn"
    assert pawn.getMaxSteps() == 1
    assert pawn.getDirections() == [(-1, 0)]
    assert pawn.getAttackDirections() == [(-1, -1), (-1, 1)]
    black_pawn = position.get_piece_at((1, 0))
    assert black_pawn.getAttackDirections() == [(1, -1), (1, 1)]


def test_english_draughts_uses_short_kings_and_12_men_each_side():
    definition = load_bundled_definition("checkers")
    position = board_from_definition(definition)
    records = [position.get_piece_at((r, c)) for r in range(8) for c in range(8)]
    assert sum(p is not None and p.getColor() == 1 for p in records) == 12
    assert sum(p is not None and p.getColor() == -1 for p in records) == 12
    from model.game.board import Board
    from model.pieces.piece import Piece

    king = Piece(
        color=1,
        piece_type="king",
        vectors=[tuple(v) for v in definition.pieces["king"]["moves"]],
        attack_vectors=[tuple(v) for v in definition.pieces["king"]["attacks"]],
        max_steps=None if definition.pieces["king"]["repeat"] else 1,
    )
    assert king.getMaxSteps() == 1


def test_separate_boards_do_not_mutate_bundled_or_other_session_state():
    definition = load_bundled_definition("chess")
    first = board_from_definition(definition)
    second = board_from_definition(definition)
    first.set_piece_at((6, 0), None)
    assert first.get_piece_at((6, 0)) is None
    assert second.get_piece_at((6, 0)).getType() == "pawn"
    assert board_from_definition(definition).get_piece_at((6, 0)).getType() == "pawn"
