"""Observable generic capture routes and non-mutating rejection behavior."""

from __future__ import annotations

import pytest

from model.game.board import Board
from model.game.capture_geometry import CaptureEnumerator
from model.game.capture_policy import CapturePolicy, EvaluationBudget, EvaluationBudgetExceeded


class CandidatePiece:
    def __init__(self, side: int):
        self.side = side

    def getColor(self):
        return self.side

    def getType(self):
        return "man"

    def getAttackDirections(self):
        return [(-1, -1), (-1, 1)]


def test_short_king_or_man_capture_does_not_modify_board():
    white = CandidatePiece(1)
    black = CandidatePiece(-1)
    board = Board((8, 8), placement=[((5, 2), white), ((4, 3), black)])
    policy = CapturePolicy(False, False, False)
    result = CaptureEnumerator(board).enumerate((5, 2), policy)
    assert result == [
        {"start": [5, 2], "steps": [{"landing": [3, 4], "captured": [4, 3]}]}
    ]
    assert board.get_piece_at((5, 2)) is white
    assert board.get_piece_at((4, 3)) is black
    assert board.get_piece_at((3, 4)) is None


def test_capture_budget_rejection_preserves_original_position():
    white = CandidatePiece(1)
    black = CandidatePiece(-1)
    board = Board((8, 8), placement=[((5, 2), white), ((4, 3), black)])
    budget = EvaluationBudget(3)
    with pytest.raises(EvaluationBudgetExceeded):
        CaptureEnumerator(board, budget).enumerate((5, 2), CapturePolicy(False, False, False))
    assert budget.used == 0
    assert board.get_piece_at((5, 2)) is white
    assert board.get_piece_at((4, 3)) is black
