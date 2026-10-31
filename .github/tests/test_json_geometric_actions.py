"""Supporting canonical geometric candidate behavior, independent of Python rules."""

from model.definition import board_from_definition, load_bundled_definition
from model.validator import MoveValidator


def test_chess_pawn_moves_follow_json_relative_vectors():
    board = board_from_definition(load_bundled_definition("chess"))
    validator = MoveValidator(board)
    white = validator.get_geometric_moves((6, 0))
    black = validator.get_geometric_moves((1, 0))
    assert (5, 0) in white
    assert (2, 0) in black
    assert (7, 0) not in white
    assert (0, 0) not in black


def test_json_based_rook_geometry_respects_initial_blockers():
    board = board_from_definition(load_bundled_definition("chess"))
    validator = MoveValidator(board)
    assert validator.get_geometric_moves((7, 0)) == []
    board.set_piece_at((6, 0), None)
    assert (6, 0) in validator.get_geometric_moves((7, 0))
    assert (0, 0) not in validator.get_geometric_moves((7, 0))


def test_geometric_candidates_never_consult_game_rule_plugins():
    board = board_from_definition(load_bundled_definition("chess"))
    validator = MoveValidator(board)

    class RuleThatMustNeverExecute:
        enabled = True

        def available_moves(self, *args):
            raise AssertionError("declarative geometry must not execute plugin code")

    validator.rules = [RuleThatMustNeverExecute()]
    assert (5, 0) in validator.get_geometric_moves((6, 0))
