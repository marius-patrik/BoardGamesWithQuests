"""Supplemental generic query/outcome contract tests (not desktop acceptance).

Actual product acceptance must separately drive game actions via the GUI.
"""

from __future__ import annotations

import pytest

from model.board import Board
from model.board_queries import BoardQueries
from model.capture_policy import EvaluationBudget, EvaluationBudgetExceeded
from model.conditions import QueryResolutionError
from model.hooks import PlannedEffect, RuleProgram
from model.outcomes import resolve_outcome
from model.piece import Piece


def board_with_piece():
    piece = Piece(
        color=1,
        piece_type="rook",
        vectors=[(1, 0), (-1, 0), (0, 1), (0, -1)],
        attack_vectors=[(1, 0), (-1, 0), (0, 1), (0, -1)],
        max_steps=None,
    )
    board = Board((6, 9), placement=[((1, 2), piece)])
    return board, piece


def test_board_queries_observe_one_rectangular_position():
    board, source_piece = board_with_piece()
    queries = BoardQueries(board, 1)
    assert queries.board_dimension({"axis": "rows"}) == 6
    assert queries.board_dimension({"axis": "columns"}) == 9
    assert queries.turn({}) == 1
    assert queries.piece_at({"square": [1, 2]}) == {"kind": "rook", "side": 1, "moved": False}
    assert queries.pieces_matching({"side": "active", "kind": "rook"}) == [
        {"square": [1, 2], "kind": "rook", "side": 1, "moved": False}
    ]
    assert queries.path_clear({"source": [1, 2], "target": [1, 8]})
    assert queries.squares_attacked({"target": [1, 8], "by_side": "active"})
    assert board.get_piece_at((1, 2)) is source_piece


def test_query_budget_is_bounded_before_expensive_board_traversal():
    board, piece = board_with_piece()
    counter = EvaluationBudget(10)
    queries = BoardQueries(board, 1, counter)
    with pytest.raises(EvaluationBudgetExceeded):
        queries.pieces_matching({})
    assert board.get_piece_at((1, 2)) is piece
    assert counter.used == 0


def test_rule_program_reads_real_board_query_not_a_private_local_map():
    board, _ = board_with_piece()
    query = BoardQueries(board, 1)
    rules = [
        {
            "id": "row-limit",
            "hook": "permits_move",
            "when": {
                "op": "compare",
                "relation": "eq",
                "left": {"query": "board_dimension", "params": {"axis": "rows"}},
                "right": 6,
            },
            "effects": [{"op": "permit", "params": {}}],
        }
    ]
    effects = (
        RuleProgram(rules)
        .evaluate("permits_move", query.bindings(), work=EvaluationBudget(1000).consume)
        .effects
    )
    assert [effect.op for effect in effects] == ["permit"]
    assert board.get_piece_at((1, 2)) is not None


def test_outcome_resolution_rejects_equal_priority_conflicts():
    draw = PlannedEffect(
        "propose_outcome",
        {
            "kind": "draw",
            "cause": "agreement",
            "winner": None,
            "priority": 30,
        },
    )
    victory = PlannedEffect(
        "propose_outcome",
        {
            "kind": "win",
            "cause": "mate",
            "winner": 1,
            "priority": 40,
        },
    )
    assert resolve_outcome((draw, victory)).winner == 1
    with pytest.raises(QueryResolutionError, match="conflicting"):
        resolve_outcome(
            (
                draw,
                PlannedEffect(
                    "propose_outcome",
                    {
                        "kind": "win",
                        "cause": "mate",
                        "winner": 1,
                        "priority": 30,
                    },
                ),
            )
        )
