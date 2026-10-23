"""Notation acceptance through the same public game actions as the desktop UI."""

from __future__ import annotations

import pytest

from model.game.notation import NotationError, render_notation, save_notation
from model.game.session import DesktopSession


def perform(session, source, target):
    state = session.snapshot()
    moves = [
        move
        for move in session.legal_actions()
        if move["start"] == list(source)
        and move["hops"][-1] == list(target)
        and move["promotion"] is None
    ]
    assert len(moves) == 1
    return session.submit(
        state["participants"][str(state["active_side"])],
        state["revision"],
        {"type": "move", "move": moves[0]},
    )["state"]


def test_chess_pgn_scholars_mate_has_san_checkmate_result_and_roster(tmp_path):
    session = DesktopSession("chess")
    for src, dst in [
        ((6, 4), (4, 4)),
        ((1, 4), (3, 4)),
        ((7, 3), (3, 7)),
        ((0, 1), (2, 2)),
        ((7, 5), (4, 2)),
        ((0, 6), (2, 5)),
        ((3, 7), (1, 5)),
    ]:
        perform(session, src, dst)
    ext, notation = render_notation(session.snapshot())
    assert ext == ".pgn"
    assert '[Event "BoardGamesWithQuests"]' in notation
    assert '[White "white"]' in notation
    assert '[Black "black"]' in notation
    assert '[Result "1-0"]' in notation
    assert "1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0" in notation
    out = tmp_path / "game.pgn"
    assert save_notation(session, out) == ".pgn"
    assert out.read_text("utf-8") == notation
    assert render_notation(DesktopSession.recover(session.snapshot()).snapshot()) == (ext, notation)


def test_english_draughts_pdn_encodes_dark_square_numbers_and_capture(tmp_path):
    session = DesktopSession("checkers")
    perform(session, (2, 3), (3, 2))
    perform(session, (5, 0), (4, 1))
    perform(session, (3, 2), (5, 0))
    extension, notation = render_notation(session.snapshot())
    assert extension == ".pdn"
    assert '[GameType "21"]' in notation
    assert "1. 10-14 21-17 2. 14x21 *" in notation
    path = tmp_path / "capture.pdn"
    save_notation(session, path)
    assert path.read_text("utf-8") == notation


def test_notation_requires_verified_snapshot_and_rejects_symlink(tmp_path):
    session = DesktopSession("chess")
    raw = session.snapshot()
    raw["board"][0]["kind"] = "untrusted"
    with pytest.raises((ValueError, TypeError)):
        render_notation(raw)
    target = tmp_path / "existing.pgn"
    target.write_text("untouched", encoding="utf-8")
    symlink = tmp_path / "link.pgn"
    symlink.symlink_to(target)
    with pytest.raises(NotationError):
        save_notation(session, symlink)
    assert target.read_text(encoding="utf-8") == "untouched"
    with pytest.raises(NotationError):
        save_notation(session, tmp_path / "wrong.pdn")


def test_pgn_black_checkmate_and_finished_game_result():
    session = DesktopSession("chess")
    for src, dst in [
        ((6, 5), (5, 5)),
        ((1, 4), (3, 4)),
        ((6, 6), (4, 6)),
        ((0, 3), (4, 7)),
    ]:
        perform(session, src, dst)
    _, notation = render_notation(session.snapshot())
    assert '[Result "0-1"]' in notation
    assert "1. f3 e5 2. g4 Qh4# 0-1" in notation



def test_published_pdn_double_corner_dyke_reference_opening():
    """Compare actual move submission/export with PDN 3.0 published example."""
    session = DesktopSession("checkers")

    def square(value):
        if not 1 <= value <= 32:
            raise AssertionError("invalid published dark square")
        row, offset = divmod(value - 1, 4)
        return (row, offset * 2 + (1 if row % 2 == 0 else 0))

    # Portable Draughts Notation 3.0 / Examples: Double Corner Dyke
    opening = [
        (9, 14), (22, 17), (11, 15), (25, 22),
        (15, 19), (23, 16), (12, 19), (24, 15),
        (10, 19), (17, 10),
    ]
    for src, dst in opening:
        perform(session, square(src), square(dst))
    state = session.snapshot()
    assert state["revision"] == len(opening)
    assert DesktopSession.recover(state).snapshot() == state
    _, exported = render_notation(state)
    expected = (
        "1. 9-14 22-17 2. 11-15 25-22 3. 15-19 23x16 "
        "4. 12x19 24x15 5. 10x19 17x10 *"
    )
    assert expected in exported
