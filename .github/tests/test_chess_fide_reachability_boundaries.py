"""Independent FIDE 2023 dead-position and checkmate-precedence acceptance.

Sources:
- FIDE 5.2.2, 6.9 and 9.6.2: https://handbook.fide.com/chapter/E012023
- Andrew Buchanan, StrateGems 18 (2002), R0093:
  https://www.janko.at/Retros/Strategems/N18.htm
- Published alive twin and legal helpmate (same Buchanan position):
  https://chess.stackexchange.com/questions/22555/is-the-dead-position-problem-solvable

Positions are specified independently of the shipped Chess JSON. They run
through the public DesktopSession, with its full bundled Chess definition.
"""

from __future__ import annotations

import time

from model.game.manager import GameManager
from model.game.session import DesktopSession
from test_chess_fide_full_definition import (
    fen_placement,
    play,
    reference_move,
    reference_position,
)

BUCHANAN_DEAD = "Bb1k1b2/bKp1p1p1/1pP1P1P1/1P6/p5P1/P7/8/8"
BUCHANAN_ALIVE = "Bb1k1b2/bKp1p1p1/1pP1P1P1/pP6/6P1/P7/8/8"
BUCHANAN_HELPMATE = (
    "b7a6", "d8e8", "a8b7", "e8d8", "b7c8", "d8e8",
    "c8d7", "e8d8", "d7e8", "d8c8", "e8f7", "c8d8",
    "f7g8", "d8e8", "a6b7", "e8d8", "g4g5", "d8e8",
    "b7c8", "a5a4", "g8f7",
)

# A constructed independent legal 150-ply sequence. Long, non-interfering
# rook tours avoid fivefold repetition while preserving a final Qb7#.
PRE_MATE = "k3r3/8/1QK5/8/8/8/8/7R"
BLACK_ROOK = ("e8", "f8", "g8", "h8", "h7", "g7", "f7", "e7", "e8")
WHITE_ROOK = (
    "h1", "g1", "f1", "e1", "e2", "e3", "e4",
    "f4", "g4", "h4", "h3", "h2", "h1",
)


def desktop_position(
    placement: str, *, to_move: str = "white", clock_seconds: int = 600
) -> DesktopSession:
    """Use the entire bundled definition with a real wall-clock session anchor."""
    reference = reference_position(
        placement, to_move=to_move, clock_seconds=clock_seconds
    )
    now_ms = time.time_ns() // 1_000_000
    fresh = GameManager(
        reference.definition, "fide-dead-position-reference", ("white", "black"), now_ms
    )
    return DesktopSession.recover(fresh.get_state())


def test_buchanan_dead_fortress_flag_fall_is_draw_not_win():
    """FIDE 5.2.2/6.9: published dead position cannot award a timeout win."""
    session = desktop_position(BUCHANAN_DEAD, clock_seconds=0)
    before = session.snapshot()
    assert fen_placement(before) == BUCHANAN_DEAD
    assert before["active_side"] == 1  # The source specifically gives White to move.
    assert before["outcome"] is None  # Current engine fails to recognize initial deadness.
    assert session.poll_timeout()
    after = session.snapshot()
    assert after["outcome"]["kind"] == "draw"
    assert after["outcome"]["winner"] is None
    assert after["revision"] == 1
    assert DesktopSession.recover(after).snapshot() == after


def test_buchanan_alive_twin_admits_published_helpmate():
    """A pawn advanced only one square distinguishes a live from a dead fortress."""
    session = desktop_position(BUCHANAN_ALIVE)
    assert fen_placement(session.snapshot()) == BUCHANAN_ALIVE
    for index, uci in enumerate(BUCHANAN_HELPMATE):
        result = play(session, uci)
        if index < len(BUCHANAN_HELPMATE) - 1:
            assert result["event"]["outcome"] is None
    last = session.snapshot()
    assert last["outcome"]["kind"] == "win"
    assert last["outcome"]["cause"] == "checkmate"
    assert last["outcome"]["winner"] == "white"
    assert len(last["events"]) == len(BUCHANAN_HELPMATE) == 21
    assert DesktopSession.recover(last).snapshot() == last


def test_buchanan_alive_twin_timeout_has_mating_possibility():
    """FIDE 6.9: White has a witnessed mate after 1.Ka6, so Black's timeout loses."""
    game = reference_position(BUCHANAN_ALIVE, clock_seconds=1)
    opening = reference_move(game, "b7a6")
    assert opening["outcome"] is None
    event = game.submit_action(
        "black", 1, "published-alive-flag", {"type": "timeout"}, 1001
    )
    assert event["outcome"]["kind"] == "win"
    assert event["outcome"]["winner"] == "white"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_checkmate_precedes_automatic_75_move_draw_at_exact_ply_150():
    """FIDE 9.6.2: mate on ply 150 overrides an otherwise automatic draw."""
    session = desktop_position(PRE_MATE, to_move="black")
    assert fen_placement(session.snapshot()) == PRE_MATE
    for ply in range(149):
        route = BLACK_ROOK if ply % 2 == 0 else WHITE_ROOK
        index = (ply // 2) % (len(route) - 1)
        result = play(session, route[index] + route[index + 1])
        assert result["event"]["outcome"] is None, (
            f"game ended prematurely at reversible ply {ply + 1}"
        )
    before = session.snapshot()
    assert before["revision"] == before["halfmove_count"] == 149
    assert before["active_side"] == 1
    assert DesktopSession.recover(before).snapshot() == before
    event = play(session, "b6b7")["event"]
    assert event["outcome"]["kind"] == "win"
    assert event["outcome"]["cause"] == "checkmate"
    assert event["outcome"]["winner"] == "white"
    after = session.snapshot()
    assert after["revision"] == after["halfmove_count"] == 150
    assert DesktopSession.recover(after).snapshot() == after
    assert session.legal_actions() == []
