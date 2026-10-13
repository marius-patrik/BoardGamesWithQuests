"""Assert game-neutral captures through shipped JSON game policies."""

import pytest

from engine.model.game.board import Board
from engine.model.game.capture_geometry import CaptureEnumerator, CapturePolicy
from engine.model.game.conditions import QueryResolutionError
from engine.model.game.configuration import load_definition
from engine.model.pieces.piece import Piece

DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def actor(side: int, kind: str = "man", flying: bool = False) -> Piece:
    return Piece(side, kind, vectors=DIRECTIONS, attack_vectors=DIRECTIONS, repeat=flying)


def policy(game: str, kind: str) -> CapturePolicy:
    return CapturePolicy.from_json(load_definition(game).pieces[kind]["capture_policy"])


def test_english_two_hop_capture_has_one_action_and_leaves_board_unchanged() -> None:
    mover, first, second = actor(1), actor(-1), actor(-1)
    board = Board((8, 8), [((5, 2), mover), ((4, 3), first), ((2, 5), second)])
    paths = CaptureEnumerator(board).enumerate((5, 2), policy("english_draughts", "man"))
    assert any(
        [tuple(step["landing"]) for step in item["steps"]] == [(3, 4), (1, 6)] for item in paths
    )
    assert board.get_piece_at((5, 2)) is mover
    assert board.get_piece_at((4, 3)) is first
    assert board.get_piece_at((2, 5)) is second


def test_english_king_lands_only_one_square_after_capture() -> None:
    board = Board((8, 8), [((5, 2), actor(1, "king")), ((4, 3), actor(-1))])
    paths = CaptureEnumerator(board).enumerate((5, 2), policy("english_draughts", "king"))
    assert {tuple(p["steps"][0]["landing"]) for p in paths} == {(3, 4)}


def test_international_flying_king_has_multiple_landing_options() -> None:
    board = Board((10, 10), [((7, 0), actor(1, "king", True)), ((5, 2), actor(-1))])
    paths = CaptureEnumerator(board).enumerate((7, 0), policy("international_checkers", "king"))
    landing = {tuple(p["steps"][0]["landing"]) for p in paths}
    assert (4, 3) in landing and (3, 4) in landing


def test_international_man_can_capture_backward() -> None:
    board = Board((10, 10), [((3, 4), actor(1)), ((4, 5), actor(-1))])
    paths = CaptureEnumerator(board).enumerate((3, 4), policy("international_checkers", "man"))
    assert any(p["steps"][0]["landing"] == [5, 6] for p in paths)


def test_capture_search_budget_fails_instead_of_truncating_legal_paths() -> None:
    board = Board((8, 8), [((5, 2), actor(1)), ((4, 3), actor(-1))])
    with pytest.raises(QueryResolutionError, match="budget"):
        CaptureEnumerator(board).enumerate((5, 2), CapturePolicy(False, False, False, max_nodes=1))
