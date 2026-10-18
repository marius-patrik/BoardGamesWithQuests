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
