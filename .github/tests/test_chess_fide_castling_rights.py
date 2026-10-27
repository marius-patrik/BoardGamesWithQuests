"""FIDE 2023 Article 3.8.2 castling reference acceptance for both sides.

Fixtures are independent complete-board Chess positions with all
bundled declarative rules retained; no test-only move geometry is used.
https://handbook.fide.com/chapter/E012023
"""

from __future__ import annotations

import pytest

from model.game.manager import GameManager
from test_chess_fide_full_definition import reference_move, reference_position, square

CASTLING_ROOKS = "r3k2r/8/8/8/8/8/8/R3K2R"


@pytest.mark.parametrize(
    ("side", "move_uci", "king_end", "rook_end", "rights"),
    [
        ("white", "e1g1", "g1", "f1", ("white_short", "white_long")),
        ("white", "e1c1", "c1", "d1", ("white_short", "white_long")),
        ("black", "e8g8", "g8", "f8", ("black_short", "black_long")),
        ("black", "e8c8", "c8", "d8", ("black_short", "black_long")),
    ],
)
def test_fide_both_sides_of_castling_both_colours(
    side: str,
    move_uci: str,
    king_end: str,
    rook_end: str,
    rights: tuple[str, str],
) -> None:
    game = reference_position(CASTLING_ROOKS, to_move=side, castling="KQkq")
    event = reference_move(game, move_uci)
    state = game.get_state()
    by_square = {tuple(piece["square"]): piece for piece in state["board"]}
    assert by_square[tuple(square(king_end))]["kind"] == "king"
    assert by_square[tuple(square(rook_end))]["kind"] == "rook"
    assert all(state["special_rights"][name] is False for name in rights)
    assert event["outcome"] is None
    assert GameManager.from_snapshot(state).get_state() == state


def test_castling_right_does_not_reappear_after_rook_and_king_return_home() -> None:
    game = reference_position(CASTLING_ROOKS, castling="KQkq")
    for uci in ("h1h2", "e8f8", "h2h1", "f8e8"):
        reference_move(game, uci)
    state = game.get_state()
    assert state["special_rights"]["white_short"] is False
    assert state["special_rights"]["white_long"] is True
    assert state["special_rights"]["black_short"] is False
    assert state["special_rights"]["black_long"] is False
    assert not any(
        list(m.start_pos) == square("e1") and list(m.end_pos) == square("g1")
        for m in game.get_valid_moves()
    )
    assert GameManager.from_snapshot(state).get_state() == state


def test_capture_on_original_rook_square_removes_castling_right() -> None:
    game = reference_position(CASTLING_ROOKS, castling="KQkq")
    event = reference_move(game, "h1h8")
    state = game.get_state()
    assert event["captured"] == [square("h8")]
    assert state["special_rights"]["white_short"] is False
    assert state["special_rights"]["black_short"] is False
    assert GameManager.from_snapshot(state).get_state() == state
