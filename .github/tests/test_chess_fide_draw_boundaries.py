"""Independently specified FIDE fifty/seventy-five-move acceptance boundaries.

FIDE Laws of Chess (2023) Articles 9.3.1, 9.3.2, 9.5.2 and 9.6.2:
https://handbook.fide.com/chapter/E012023

The fixed legal king tours have coprime-ish lengths (10 and 12), so the full
position, including whose turn it is, recurs only every 120 plies. Neither
king approaches the opposing rook's attack line. Two rooks remain available
to give mate; there are no pawns or captures. Thus these tests cannot be
prematurely terminated by threefold/fivefold, dead position or a pawn reset.
All game rules are the actual bundled Chess definition, not test stubs.
"""

from __future__ import annotations

import pytest

from model.game.manager import GameManager, TransitionError
from test_chess_fide_full_definition import reference_position, square

FIDE_KINGS_AND_ROOKS = "4k3/8/8/R7/7r/8/8/K7"
WHITE_KING_TOUR = ("a1", "b1", "c1", "d1", "d2", "d3", "c3", "b3", "a3", "a2", "a1")
BLACK_KING_TOUR = (
    "e8",
    "e7",
    "e6",
    "f6",
    "g6",
    "h6",
    "h7",
    "h8",
    "g8",
    "g7",
    "f7",
    "f8",
    "e8",
)


def _quiet_king_move(game: GameManager, ply: int) -> dict:
    route = WHITE_KING_TOUR if ply % 2 == 0 else BLACK_KING_TOUR
    index = (ply // 2) % (len(route) - 1)
    origin, destination = square(route[index]), square(route[index + 1])
    matches = [
        move
        for move in game.get_valid_moves()
        if list(move.start_pos) == origin and list(move.end_pos) == destination
    ]
    assert len(matches) == 1, f"independently legal king tour failed at ply {ply + 1}"
    state = game.get_state()
    actor = state["participants"][str(state["active_side"])]
    result = game.submit(actor, state["revision"], f"fide-quiet-{ply}", matches[0], ply + 1)
    assert result["captured"] == []
    return result


def _advance(game: GameManager, start: int, end: int) -> None:
    for ply in range(start, end):
        event = _quiet_king_move(game, ply)
        assert event["outcome"] is None, f"premature automatic draw at ply {ply + 1}"


def _claim(game: GameManager, *, intended_move: dict | None, action_id: str) -> dict:
    state = game.get_state()
    actor = state["participants"][str(state["active_side"])]
    return game.submit_action(
        actor,
        state["revision"],
        action_id,
        {"type": "claim_draw", "claim": "fifty-move", "intended_move": intended_move},
        state["revision"] + 1,
    )


def _reject_current_claim_atomically(game: GameManager) -> None:
    before = game.get_state()
    with pytest.raises(TransitionError):
        _claim(game, intended_move=None, action_id=f"fide-early-{before['revision']}")
    assert game.get_state() == before


def test_fifty_move_current_and_prospective_claims_on_exact_boundaries():
    game = reference_position(FIDE_KINGS_AND_ROOKS)
    _advance(game, 0, 98)
    _reject_current_claim_atomically(game)  # 49 moves by each side, not yet 50.
    _advance(game, 98, 99)
    _reject_current_claim_atomically(game)  # Exactly 99 reversible halfmoves.

    before = game.get_state()
    expected_origin = square("e7")
    expected_end = square("e6")
    intentions = [
        m
        for m in game.get_valid_moves()
        if list(m.start_pos) == expected_origin and list(m.end_pos) == expected_end
    ]
    assert len(intentions) == 1
    proposal = intentions[0].to_json()
    result = _claim(game, intended_move=proposal, action_id="fide-fifty-prospective-99")
    assert result["outcome"]["kind"] == "draw"
    assert result["outcome"]["cause"] == "fifty-move"
    assert result["move"] is None
    assert game.get_state()["board"] == before["board"]
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()

    # A different copy actually makes the 100th halfmove and claims the
    # already-established threshold on the following player's turn.
    completed = GameManager.from_snapshot(before)
    _advance(completed, 99, 100)
    at_boundary = completed.get_state()
    assert at_boundary["outcome"] is None
    result = _claim(completed, intended_move=None, action_id="fide-fifty-current-100")
    assert result["outcome"]["kind"] == "draw"
    assert result["outcome"]["cause"] == "fifty-move"
    assert completed.get_state()["board"] == at_boundary["board"]
    assert GameManager.from_snapshot(completed.get_state()).get_state() == completed.get_state()


def test_seventy_five_move_automatic_draw_is_at_150_not_149_halfmoves():
    game = reference_position(FIDE_KINGS_AND_ROOKS)
    _advance(game, 0, 149)
    at_149 = game.get_state()
    assert at_149["outcome"] is None
    assert at_149["revision"] == 149
    assert GameManager.from_snapshot(at_149).get_state() == at_149

    result = _quiet_king_move(game, 149)
    assert result["outcome"] is not None
    assert result["outcome"]["kind"] == "draw"
    assert result["outcome"]["cause"] == "seventy-five-move"
    final = game.get_state()
    assert final["revision"] == 150
    assert len(final["events"]) == 150
    assert GameManager.from_snapshot(final).get_state() == final
