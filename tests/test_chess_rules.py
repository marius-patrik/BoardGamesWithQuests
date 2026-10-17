<<<<<<< HEAD
"""FIDE articles 1/3/5/6/9 exercised through authoritative JSON transitions.

Focused fixtures select bundled rule subsets to isolate independent facets; the
opening gate uses the complete shipped definition and the production budget.
"""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from engine.model.game.configuration import validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move

CONFIG = Path(__file__).parents[1] / "packages/chess/config.json"


def configuration():
    """Return an independent copy of the shipped declarative rulebook."""
    return json.loads(CONFIG.read_text())


def session(placement=None, *, side=1, offers=(), outcomes=(), targets=None):
    """Build a consumer-authored test position with explicit rule dependencies."""
    data = configuration()
    if placement is None:
        return GameManager(validate_definition(data), "chess", ("white", "black"), 0)
    data["starting_side"] = side
    data["board"]["starting_pieces"] = [
        {"piece": kind, "color": "white" if color == 1 else "black", "squares": [square]}
        for kind, color, square in placement
    ]
    data["rules"] = [
        rule
        for rule in data["rules"]
        if rule["hook"] == "permits_move" or rule["id"] in offers or rule["id"] in outcomes
    ]
    if targets:
        data["initial_state"]["temporary_targets"].update(targets)
    return GameManager(validate_definition(data), "chess", ("white", "black"), 0)


def play(game, start, end, promotion=None):
    """Submit a move as the actual active participant at a monotonic trusted time."""
    state = game.get_state()
    actor = state["participants"][str(state["active_side"])]
    return game.submit(
        actor,
        state["revision"],
        "move-" + str(state["revision"]),
        Move(tuple(start), tuple(end), promotion=promotion),
        state["revision"] + 1,
    )


def reject(game, start, end, promotion=None):
    """Prove an illegal intent leaves the complete persistence envelope unchanged."""
    before = game.get_state()
    with pytest.raises(TransitionError):
        play(game, start, end, promotion)
    assert game.get_state() == before


def test_complete_opening_has_twenty_moves_and_e4_recovers():
    """Articles 2/3: the complete shipped rulebook must work within production bounds."""
    game = session()
    assert len(game.get_valid_moves()) == 20
    play(game, [6, 4], [4, 4])
    snapshot = game.get_state()
    assert snapshot["temporary_targets"]["en_passant"] == [5, 4]
    assert GameManager.from_snapshot(snapshot).get_state() == snapshot


@pytest.mark.parametrize("side,start,end", [(1, [6, 2], [4, 2]), (-1, [1, 2], [3, 2])])
def test_pawn_first_double_and_immediate_target(side, start, end):
    color = "white" if side == 1 else "black"
    game = session(
        [("king", 1, [7, 4]), ("king", -1, [0, 4]), ("pawn", side, start)],
        side=side,
        offers=[color + "-double-2"],
    )
    play(game, start, end)
    assert game.get_state()["temporary_targets"]["en_passant"] == [(start[0] + end[0]) // 2, 2]
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


@pytest.mark.parametrize("block", [[5, 2], [4, 2]])
def test_blocked_double_is_illegal_and_atomic(block):
    game = session(
        [("king", 1, [7, 4]), ("king", -1, [0, 4]), ("pawn", 1, [6, 2]), ("knight", -1, block)],
        offers=["white-double-2"],
    )
    reject(game, [6, 2], [4, 2])


@pytest.mark.parametrize("end", [[5, 1], [5, 3]])
def test_pawn_diagonal_empty_square_cannot_be_captured(end):
    game = session([("king", 1, [7, 4]), ("king", -1, [0, 4]), ("pawn", 1, [6, 2])])
    reject(game, [6, 2], end)


def test_pawn_cannot_capture_straight_ahead_or_expose_pinned_king():
    game = session(
        [
            ("king", 1, [7, 4]),
            ("king", -1, [0, 0]),
            ("pawn", 1, [6, 4]),
            ("rook", -1, [0, 4]),
            ("knight", -1, [5, 4]),
        ]
    )
    reject(game, [6, 4], [5, 4])
    reject(game, [6, 4], [5, 3])


@pytest.mark.parametrize("side,row,rank", [(1, 1, 0), (-1, 6, 7)])
@pytest.mark.parametrize("promotion", ["queen", "rook", "bishop", "knight"])
def test_every_promotion_choice_immediately_replaces_pawn(side, row, rank, promotion):
    game = session([("king", 1, [7, 7]), ("king", -1, [0, 7]), ("pawn", side, [row, 0])], side=side)
    play(game, [row, 0], [rank, 0], promotion)
    assert any(
        piece["square"] == [rank, 0] and piece["kind"] == promotion and piece["side"] == side
        for piece in game.get_state()["board"]
    )
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


@pytest.mark.parametrize("promotion", [None, "king", "pawn", "unknown"])
def test_promotion_requires_exact_legal_choice(promotion):
    game = session([("king", 1, [7, 7]), ("king", -1, [0, 7]), ("pawn", 1, [1, 0])])
    reject(game, [1, 0], [0, 0], promotion)


@pytest.mark.parametrize("pinned", [False, True])
def test_en_passant_auxiliary_capture_and_discovered_check(pinned):
    pieces = [
        ("king", 1, [3, 0] if pinned else [7, 0]),
        ("king", -1, [0, 0]),
        ("pawn", 1, [3, 2]),
        ("pawn", -1, [3, 3]),
    ]
    if pinned:
        pieces.append(("rook", -1, [3, 7]))
    game = session(pieces, offers=["white-passing-2-1"], targets={"en_passant": [2, 3]})
    if pinned:
        reject(game, [3, 2], [2, 3])
    else:
        event = play(game, [3, 2], [2, 3])
        assert event["captured"] == [[3, 3]]
        assert not any(piece["square"] == [3, 3] for piece in game.get_state()["board"])
        assert game.get_state()["temporary_targets"]["en_passant"] is None
        assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


@pytest.mark.parametrize("side,row", [(1, 7), (-1, 0)])
@pytest.mark.parametrize("wing,rook,end,rookend", [("short", 7, 6, 5), ("long", 0, 2, 3)])
def test_castling_moves_both_pieces_and_consumes_rights(side, row, wing, rook, end, rookend):
    color = "white" if side == 1 else "black"
    game = session(
        [("king", side, [row, 4]), ("rook", side, [row, rook]), ("king", -side, [7 - row, 4])],
        side=side,
        offers=[color + "-castle-" + wing],
        outcomes=[color + "-short-rights", color + "-long-rights"],
    )
    play(game, [row, 4], [row, end])
    state = game.get_state()
    assert any(p["square"] == [row, rookend] and p["kind"] == "rook" for p in state["board"])
    assert (
        state["special_rights"][color + "_short"] is False
        and state["special_rights"][color + "_long"] is False
    )
    assert GameManager.from_snapshot(state).get_state() == state


@pytest.mark.parametrize("attacked_file", [4, 5, 6])
def test_castling_out_of_through_or_into_check_rejects(attacked_file):
    game = session(
        [
            ("king", 1, [7, 4]),
            ("rook", 1, [7, 7]),
            ("king", -1, [0, 0]),
            ("rook", -1, [0, attacked_file]),
        ],
        offers=["white-castle-short"],
    )
    reject(game, [7, 4], [7, 6])


def test_adjacent_kings_and_king_capture_are_rejected():
    game = session([("king", 1, [4, 4]), ("king", -1, [2, 4]), ("rook", 1, [2, 0])])
    reject(game, [4, 4], [3, 4])
    reject(game, [2, 0], [2, 4])


@pytest.mark.parametrize("mate", [True, False])
def test_checkmate_and_stalemate_use_actual_legal_escape_set(mate):
    # Black king a8, white king c6. Qb7 mates; Qc7 stalemates.
    game = session(
        [("king", -1, [0, 0]), ("king", 1, [2, 2]), ("queen", 1, [2, 1] if mate else [2, 3])],
        outcomes=["checkmate", "stalemate"],
    )
    event = play(game, [2, 1] if mate else [2, 3], [1, 1] if mate else [1, 2])
    assert event["outcome"]["kind"] == ("win" if mate else "draw")
    assert event["outcome"]["winner"] == ("white" if mate else None)
    assert game.get_valid_moves() == []
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_promotion_capture_removes_rook_and_resets_halfmove():
    game = session(
        [("king", 1, [7, 7]), ("king", -1, [0, 7]), ("pawn", 1, [1, 1]), ("rook", -1, [0, 0])]
    )
    event = play(game, [1, 1], [0, 0], "knight")
    assert event["captured"] == [[0, 0]]
    assert game.get_state()["halfmove_count"] == 0
    assert any(
        p["square"] == [0, 0] and p["kind"] == "knight" and p["side"] == 1
        for p in game.get_state()["board"]
    )


def test_castling_right_cannot_return_after_rook_moves_back():
    game = session(
        [("king", 1, [7, 4]), ("rook", 1, [7, 7]), ("king", -1, [0, 4])],
        offers=["white-castle-short"],
        outcomes=["white-short-rights", "white-long-rights"],
    )
    play(game, [7, 7], [6, 7])
    play(game, [0, 4], [0, 3])
    play(game, [6, 7], [7, 7])
    play(game, [0, 3], [0, 4])
    assert game.get_state()["special_rights"]["white_short"] is False
    reject(game, [7, 4], [7, 6])


def test_en_passant_expires_after_any_intervening_move():
    game = session(
        [("king", 1, [7, 0]), ("king", -1, [0, 0]), ("pawn", 1, [3, 2]), ("pawn", -1, [3, 3])],
        offers=["white-passing-2-1"],
        targets={"en_passant": [2, 3]},
    )
    play(game, [7, 0], [7, 1])
    play(game, [0, 0], [0, 1])
    reject(game, [3, 2], [2, 3])


@pytest.mark.parametrize("side", [1, -1])
def test_resignation_uses_actual_actor_and_retries_after_restart(side):
    game = session(
        [("king", 1, [7, 4]), ("rook", 1, [7, 7]), ("king", -1, [0, 4]), ("rook", -1, [0, 7])],
        outcomes=["resignation"],
    )
    actor = "white" if side == 1 else "black"
    event = game.submit_action(actor, 0, "resign", {"type": "resign"}, 1)
    assert event["outcome"]["winner"] == ("black" if side == 1 else "white")
    snapshot = game.get_state()
    recovered = GameManager.from_snapshot(snapshot)
    assert recovered.submit_action(actor, 0, "resign", {"type": "resign"}, 999) == event
    assert recovered.get_state() == snapshot


def test_threefold_claim_after_repeated_knight_cycles():
    game = session(
        [("king", 1, [7, 4]), ("king", -1, [0, 4]), ("knight", 1, [7, 6]), ("knight", -1, [0, 6])],
        outcomes=["threefold", "fivefold"],
    )
    for _ in range(2):
        for start, end in (([7, 6], [5, 5]), ([0, 6], [2, 5]), ([5, 5], [7, 6]), ([2, 5], [0, 6])):
            play(game, start, end)
    before = game.get_state()
    event = game.submit_action(
        "white", 8, "draw", {"type": "claim_draw", "claim": "threefold", "intended_move": None}, 9
    )
    assert event["outcome"]["kind"] == "draw"
    assert game.get_state()["board"] == before["board"]
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


@pytest.mark.parametrize(
    "rule_id,halfmove_limit,claim_draw",
    [("fifty-move", 100, True), ("seventy-five-move", 150, False)],
)
def test_reversible_move_thresholds_require_exact_number_of_halfmoves(
    rule_id, halfmove_limit, claim_draw
):
    game = session(
        [("king", 1, [7, 4]), ("king", -1, [0, 4]), ("knight", 1, [7, 6]), ("knight", -1, [0, 6])],
        outcomes=[rule_id],
    )
    if claim_draw:
        before = game.get_state()
        with pytest.raises(TransitionError):
            game.submit_action(
                "white",
                0,
                "premature",
                {"type": "claim_draw", "claim": rule_id, "intended_move": None},
                1,
            )
        assert game.get_state() == before
    cycle = (([7, 6], [5, 5]), ([0, 6], [2, 5]), ([5, 5], [7, 6]), ([2, 5], [0, 6]))
    for index in range(halfmove_limit):
        event = play(game, *cycle[index % 4])
        if index < halfmove_limit - 1:
            assert event["outcome"] is None
    if claim_draw:
        event = game.submit_action(
            "white",
            halfmove_limit,
            "claim",
            {"type": "claim_draw", "claim": rule_id, "intended_move": None},
            halfmove_limit + 1,
        )
    assert event["outcome"]["kind"] == "draw"
    assert event["outcome"]["cause"] == rule_id
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_fivefold_repetition_is_automatic_without_claim():
    game = session(
        [("king", 1, [7, 4]), ("king", -1, [0, 4]), ("knight", 1, [7, 6]), ("knight", -1, [0, 6])],
        outcomes=["fivefold"],
    )
    for index in range(16):
        event = play(
            game,
            *(([7, 6], [5, 5]), ([0, 6], [2, 5]), ([5, 5], [7, 6]), ([2, 5], [0, 6]))[index % 4],
        )
        if index < 15:
            assert event["outcome"] is None
    assert event["outcome"]["cause"] == "fivefold"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


@pytest.mark.parametrize("minor", ["bishop", "knight"])
def test_king_and_single_minor_is_dead_after_legal_move(minor):
    game = session(
        [("king", 1, [7, 4]), ("king", -1, [0, 4]), (minor, 1, [6, 0])], outcomes=["dead-material"]
    )
    event = play(game, [7, 4], [7, 5])
    assert event["outcome"]["kind"] == "draw" and event["outcome"]["cause"] == "dead-material"


@pytest.mark.parametrize("same_color", [True, False])
def test_bishop_square_colors_affect_dead_material(same_color):
    game = session(
        [
            ("king", 1, [7, 4]),
            ("king", -1, [0, 4]),
            ("bishop", 1, [6, 0]),
            ("bishop", -1, [1, 1] if same_color else [1, 2]),
        ],
        outcomes=["same-color-bishops"],
    )
    event = play(game, [7, 4], [7, 5])
    assert (event["outcome"] is not None) == same_color


def test_resignation_against_bare_king_is_draw():
    game = session(
        [("king", 1, [7, 4]), ("queen", 1, [7, 3]), ("king", -1, [0, 4])],
        outcomes=["resignation", "resignation-draw"],
    )
    event = game.submit_action("white", 0, "resign", {"type": "resign"}, 1)
    assert event["outcome"]["kind"] == "draw" and event["outcome"]["winner"] is None


@pytest.mark.parametrize("minor", ["knight", "bishop"])
@pytest.mark.parametrize("expired_side", [-1, 1])
def test_timeout_in_familiar_dead_material_is_draw_not_opponents_win(minor, expired_side):
    data = configuration()
    data["clock"]["initial_seconds"] = 0
    data["starting_side"] = expired_side
    data["board"]["starting_pieces"] = [
        {"piece": "king", "color": "white", "squares": [[7, 7]]},
        {"piece": minor, "color": "white", "squares": [[6, 0]]},
        {"piece": "king", "color": "black", "squares": [[0, 0]]},
    ]
    data["rules"] = [
        r
        for r in data["rules"]
        if r["hook"] == "permits_move"
        or r["id"] == "dead-material"
        or r["id"].startswith("timeout-")
    ]
    game = GameManager(validate_definition(data), "timeout", ("white", "black"), 0)
    event = game.submit_action("black", 0, "flag", {"type": "timeout"}, 0)
    assert event["outcome"]["kind"] == "draw" and event["outcome"]["winner"] is None
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()
||||||| b45d2e0f
=======
"""The chess rules, exercised as rules.

Every case here sets up a position and asks a rule a question. Nothing reaches into a rule's
internals, because the point of the rule layer is that a rule is asked rather than inspected.
"""

from games.chess.board import build_board
from model.game.board import Board
from model.game.move import Move
from model.game.validator import MoveValidator
from games.chess.pieces.bishop import Bishop
from games.chess.pieces.knight import Knight
from games.chess.pieces.king import King
from games.chess.pieces.pawn import Pawn
from games.chess.pieces.queen import Queen
from games.chess.pieces.rook import Rook
from games.chess.rules import build_rules
from games.chess.rules.attacks import has_legal_move
from games.chess.rules.check import in_check
from games.chess.rules.castling import CASTLE_KING_SIDE, CASTLE_QUEEN_SIDE, CastlingRule
from games.chess.rules.en_passant import EnPassantRule
from games.chess.rules.draws import (
    FiftyMoveRule,
    InsufficientMaterialRule,
    MutualAgreementRule,
    ThreefoldRepetitionRule,
)
from games.chess.rules.flag import FlagFallRule
from games.chess.rules.promotion import PromotionRule


def empty_board():
    """Return a board with no pieces on it."""
    return Board(setup_pieces=False)


def castling_ready_board(king_file=4):
    """Return a board where White may castle either way.

    Args:
        king_file: The file the white king stands on.

    Returns:
        Board: A board with both white rooks and the white king on their home squares.
    """
    board = empty_board()
    board.set_piece_at((0, king_file), King(1))
    board.set_piece_at((0, 0), Rook(1))
    board.set_piece_at((0, 7), Rook(1))
    board.set_piece_at((7, 4), King(-1))
    return board


def test_chess_declares_thirteen_rules_in_a_fixed_order():
    """The set of rules in force is closed, ordered, and written out by hand."""
    rules = build_rules()
    assert [rule.default_name for rule in rules] == [
        "Royal piece",
        "Castling",
        "En passant",
        "Promotion",
        "Bishop colour",
        "Check",
        "Checkmate",
        "Stalemate",
        "Insufficient material",
        "Fifty-move rule",
        "Threefold repetition",
        "Draw by agreement",
        "Flag fall",
    ]


def test_check_is_reported_while_the_game_continues():
    """Check is a status, not an outcome: the player is still allowed to move."""
    board = empty_board()
    board.set_piece_at((0, 4), King(1))
    board.set_piece_at((7, 4), Rook(-1))

    rules = build_rules()
    rule = next(r for r in rules if r.default_name == "Check")
    rule.active_color = 1

    assert in_check(board, 1) is True
    assert rule.status(board) == "Check"
    assert rule.outcome(board) is None
    assert has_legal_move(board, 1, rules) is True


def test_checkmate_ends_the_game_for_the_opponent():
    """Mate is a win for the other side, and it outranks the draws."""
    board = empty_board()
    board.set_piece_at((0, 0), King(1))
    board.set_piece_at((0, 1), Queen(-1))
    board.set_piece_at((1, 1), Rook(-1))

    rules = build_rules()
    MoveValidator(board, rules=rules)  # the validator hands each rule the rule set
    mate = next(r for r in rules if r.default_name == "Checkmate")
    mate.active_color = 1
    result = mate.outcome(board)

    assert result is not None
    assert result.kind == "win"
    assert result.winner == -1
    assert result.reason == "checkmate"
    assert has_legal_move(board, 1, rules) is False


def test_stalemate_is_a_draw_and_not_a_loss():
    """Stuck without being attacked is a draw, which is a different answer from mate."""
    board = empty_board()
    board.set_piece_at((0, 0), King(1))
    board.set_piece_at((1, 2), Queen(-1))
    board.set_piece_at((2, 2), King(-1))

    rules = build_rules()
    MoveValidator(board, rules=rules)
    stale = next(r for r in rules if r.default_name == "Stalemate")
    stale.active_color = 1
    result = stale.outcome(board)

    assert result is not None
    assert result.kind == "draw"
    assert result.reason == "stalemate"
    assert in_check(board, 1) is False


def test_the_opening_position_leaves_nobody_in_check():
    """Neither king starts attacked, so no status fires before the first move."""
    board = build_board()
    assert in_check(board, 1) is False
    assert in_check(board, -1) is False


def test_castling_is_offered_on_both_sides_and_moves_the_rook():
    """A castle carries the rook, which is why it needs a companion square."""
    board = castling_ready_board()
    rule = CastlingRule()

    offered = rule.available_moves(board, board.get_piece_at((0, 4)))
    assert [m.move_type for m in offered] == ["castling", "castling"]

    kingside, queenside = offered
    assert (kingside.end_pos, kingside.companion_start, kingside.companion_end) == (
        (0, 6),
        (0, 7),
        (0, 5),
    )
    assert (queenside.end_pos, queenside.companion_start, queenside.companion_end) == (
        (0, 2),
        (0, 0),
        (0, 3),
    )


def test_castling_is_withheld_when_the_king_would_cross_an_attacked_square():
    """The king may not pass through check, so the transit square decides."""
    board = castling_ready_board()
    board.set_piece_at((5, 5), Rook(-1))  # attacks f1, the square the king crosses
    rule = CastlingRule()

    offered = rule.available_moves(board, board.get_piece_at((0, 4)))
    assert [m.end_pos for m in offered] == [(0, 2)]  # queenside only


def test_castling_is_withdrawn_once_the_king_has_moved():
    """Rights are lost by moving the king, and remembered by the rule itself."""
    board = castling_ready_board()
    rule = CastlingRule()
    rule.attach()
    king = board.get_piece_at((0, 4))

    assert rule.available_moves(board, king) != []

    board.move_piece((0, 4), (1, 4))
    king.setMoved()
    rule.on_move_made(board, Move((0, 4), (1, 4), piece=king))

    assert rule.available_moves(board, board.get_piece_at((1, 4))) == []


def test_castling_is_withheld_when_the_path_is_occupied():
    """A blocked square means no castle, even though nothing is attacking."""
    board = castling_ready_board()
    board.set_piece_at((0, 5), Bishop(-1))
    rule = CastlingRule()

    assert CASTLE_KING_SIDE not in [
        m.move_type for m in rule.available_moves(board, board.get_piece_at((0, 4)))
    ]


def test_en_passant_is_offered_only_on_the_ply_after_a_double_advance():
    """The capture is available for exactly one move, and lifts the pawn from where it stands."""
    board = empty_board()
    white_pawn = Pawn(1)
    black_pawn = Pawn(-1)
    board.set_piece_at((4, 3), white_pawn)  # d5, the pawn that will capture
    board.set_piece_at((4, 4), black_pawn)  # e5, where the black pawn now stands
    board.set_piece_at((7, 4), King(-1))
    board.set_piece_at((0, 0), King(1))

    rule = EnPassantRule()
    rule.attach()
    # Black advanced e7 (6,4) to e5 (4,4) by its declared one-off long step.
    rule.on_move_made(board, Move((6, 4), (4, 4), piece=black_pawn))

    assert rule.victim_square() == (4, 4)
    offered = rule.available_moves(board, white_pawn)

    assert len(offered) == 1
    capture = offered[0]
    assert (capture.start_pos, capture.end_pos) == ((4, 3), (5, 4))  # d5 takes on e6
    assert capture.move_type == "en_passant"
    assert capture.capture_from == (4, 4)  # the black pawn is lifted from e5, not e6


def test_en_passant_expires_when_another_move_is_played():
    """One ply only: any other move takes the offer away."""
    board = empty_board()
    white_pawn = Pawn(1)
    black_pawn = Pawn(-1)
    board.set_piece_at((4, 3), white_pawn)
    board.set_piece_at((4, 4), black_pawn)

    rule = EnPassantRule()
    rule.attach()
    rule.on_move_made(board, Move((6, 4), (4, 4), piece=black_pawn))
    assert rule.available_moves(board, white_pawn) != []

    # A quiet move by either side ends the offer.
    board.set_piece_at((7, 0), Rook(1))
    rule.on_move_made(board, Move((6, 0), (7, 0), piece=board.get_piece_at((7, 0))))

    assert rule.victim_square() is None
    assert rule.available_moves(board, white_pawn) == []


def test_promotion_is_offered_to_the_four_choices():
    """A pawn reaching the far rank is offered a promotion, not left a pawn."""
    board = empty_board()
    pawn = Pawn(1)
    board.set_piece_at((6, 4), pawn)  # e7, one step from promoting

    rule = PromotionRule()
    offered = rule.available_moves(board, pawn)

    assert offered != []
    assert all(m.promotion_piece is not None for m in offered)
    # The promoted knight reports the `horse` descriptor; the class is `Knight`. The two
    # spellings are bridged where a rule compares kinds, and `Horse` is not a name here.
    assert {m.promotion_piece.getType() for m in offered} == {"queen", "rook", "bishop", "horse"}
    assert {type(m.promotion_piece).__name__ for m in offered} == {
        "Queen",
        "Rook",
        "Bishop",
        "Knight",
    }


def test_the_validator_asks_the_rules_rather_than_guessing():
    """With chess in force the engine knows a king; with no rules it knows nothing."""
    board = build_board()

    with_chess = MoveValidator(board, rules=build_rules())
    assert with_chess.royal_kinds() == ["king"]
    assert with_chess.find_royal(1) == (0, 4)

    without_rules = MoveValidator(board)
    assert without_rules.royal_kinds() == []
    assert without_rules.find_royal(1) is None
    assert without_rules.is_check(1) is False


def test_a_knight_is_judged_by_its_declared_vectors_not_its_name():
    """The knight is a knight to the player and only a leaping piece to the engine."""
    board = empty_board()
    board.set_piece_at((4, 4), Knight(1))

    assert in_check(board, -1, royal_kind="king") is False
    assert MoveValidator(board).get_valid_moves((4, 4)) != []


def kings_only_board():
    """Return a board holding just the two kings."""
    board = empty_board()
    board.set_piece_at((0, 0), King(1))
    board.set_piece_at((7, 7), King(-1))
    return board


def insufficient_outcome(*white_extra):
    """Judge a position where Black has only a king.

    Args:
        *white_extra: The (square, piece) pairs White has besides its king.

    Returns:
        Optional[Result]: The rule's answer for that position.
    """
    board = kings_only_board()
    for square, piece in white_extra:
        board.set_piece_at(square, piece)
    rule = InsufficientMaterialRule()
    rule.attach()
    rule.active_color = 1
    return rule.outcome(board)


def test_insufficient_material_draws_the_positions_that_cannot_be_mated():
    """A side that can never mate is a draw, whatever the pieces happen to be."""
    # (4, 4) and (4, 5) are one square colour apart; (4, 4) and (4, 3) are too, but the
    # bishops below are placed on squares of the same parity on purpose.
    assert insufficient_outcome() is not None
    assert insufficient_outcome(((4, 4), Knight(1))) is not None
    assert insufficient_outcome(((4, 4), Bishop(1))) is not None
    assert insufficient_outcome(((4, 0), Bishop(1)), ((5, 1), Bishop(1))) is not None

    assert insufficient_outcome(((4, 4), Rook(1))) is None
    assert insufficient_outcome(((4, 4), Knight(1)), ((3, 4), Knight(1))) is None
    assert insufficient_outcome(((4, 0), Bishop(1)), ((4, 1), Bishop(1))) is None


def test_the_knight_is_recognised_by_either_spelling_of_its_kind():
    """A setting written for `knight` still matches the piece that reports `knight`."""
    board = kings_only_board()
    board.set_piece_at((4, 4), Knight(1))
    rule = InsufficientMaterialRule()
    rule.attach()
    rule.active_color = 1
    assert rule.outcome(board) is not None


def test_fifty_moves_without_progress_is_a_draw():
    """The half-move clock is kept by the rule and read by the rule."""
    board = kings_only_board()
    rule = FiftyMoveRule()
    rule.attach()
    rule.active_color = 1

    king = board.get_piece_at((0, 0))
    for _ in range(99):
        rule.on_move_made(board, Move((0, 0), (0, 1), piece=king))
    assert rule.outcome(board) is None

    rule.on_move_made(board, Move((0, 0), (0, 1), piece=king))
    result = rule.outcome(board)
    assert result is not None
    assert result.kind == "draw"
    assert result.reason == "fifty-move rule"


def test_threefold_repetition_counts_a_position_it_has_already_seen():
    """Asking whether the game is over must not itself create the repetition."""
    board = kings_only_board()
    rule = ThreefoldRepetitionRule()
    rule.attach()
    rule.active_color = 1

    assert rule.record(board) == 1
    assert rule.outcome(board) is None
    assert rule.record(board) == 1  # idempotent for the position being judged
    assert rule.outcome(board) is None


def test_a_draw_offer_only_draws_the_game_once_it_is_accepted():
    """An offer on the table is not a result."""
    board = kings_only_board()
    rule = MutualAgreementRule()
    rule.attach()
    rule.active_color = 1

    assert rule.outcome(board) is None

    rule.offer()
    assert rule.outcome(board) is None

    rule.accept()
    result = rule.outcome(board)
    assert result is not None
    assert result.kind == "draw"


def test_flag_fall_stays_silent_when_there_is_no_clock_to_fall():
    """With no clock attached there is no time to have run out."""
    board = kings_only_board()
    rule = FlagFallRule()
    rule.attach()
    rule.active_color = 1
    assert rule.outcome(board) is None
>>>>>>> fix/independent-review-findings
