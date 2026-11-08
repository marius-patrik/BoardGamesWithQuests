"""Actual Tkinter window and board controls, executed under Xvfb on Linux CI."""

import os
import tkinter as tk
import pytest
from view.app import BoardGamesApplication

pytestmark = pytest.mark.gui


def application(tmp_path):
    try:
        app = BoardGamesApplication(tmp_path)
    except tk.TclError as exc:
        pytest.skip(f"Graphical display unavailable: {exc}")
    app.users.vytvor_uzivatele("alice", "Alice")
    app.users.vytvor_uzivatele("bob", "Bob")
    app.show_setup()
    app.seat_choices["white"].set("alice")
    app.seat_choices["black"].set("bob")
    app.start_match()
    app.update()
    return app


def test_setup_and_button_board_move(tmp_path):
    app = application(tmp_path)
    try:
        assert len(app.board.buttons) == 64
        app.board.buttons[(6, 4)].invoke()
        app.update()
        assert (4, 4) in app.controller.destinace
        app.board.buttons[(4, 4)].invoke()
        app.update()
        assert app.manager.aktivni_barva == "black"
        assert "e2" in app.history.get("1.0", "end")
        assert app.manager.logger.path.exists()
    finally:
        app.destroy()


def test_keyboard_board_focus_and_cancel_selection(tmp_path):
    app = application(tmp_path)
    try:
        assert app.board._focus((6, 4)) == "break"
        app.board.buttons[(6, 4)].invoke()
        app.update()
        assert app.controller.vybrane == (6, 4)
        app.controller.zrus_vyber()
        assert app.controller.vybrane is None
        assert app.manager.revision == 0
    finally:
        app.destroy()


def test_terminal_display(tmp_path):
    app = application(tmp_path)
    try:
        app.controller.odstup()
        app.update()
        assert app.manager.stav == "terminal"
        assert "GAME OVER" in app.turn["text"]
        assert "disabled" in app.resign_button.state()
    finally:
        app.destroy()


def test_real_promotion_dialog_commits_only_after_choice(tmp_path):
    from model.board import HerniPlocha
    from model.piece import Kral, Pesak, Vez

    app = application(tmp_path)
    try:
        b = HerniPlocha(False)
        b.poloz((7, 7), Kral("white"))
        b.poloz((0, 7), Kral("black"))
        b.poloz((1, 0), Pesak("white"))
        app.manager.plocha = b
        app.refresh()
        app.board.buttons[(1, 0)].invoke()
        app.board.buttons[(0, 0)].invoke()
        app.update()
        dialogs = [c for c in app.winfo_children() if isinstance(c, tk.Toplevel)]
        assert len(dialogs) == 1
        assert app.manager.revision == 0
        buttons = [
            b
            for w in dialogs[0].winfo_children()
            for b in w.winfo_children()
            if isinstance(b, tk.ttk.Button)
        ]
        assert len(buttons) == 4
        next(b for b in buttons if b.cget("text") == "Rook").invoke()
        app.update()
        assert app.manager.revision == 1
        assert isinstance(app.manager.plocha.vrat_obsah((0, 0)), Vez)
        assert app.users.uzivatele["alice"].xp >= 25
    finally:
        app.destroy()


def test_real_gui_save_error_and_retry_feedback(tmp_path):
    from unittest.mock import patch

    app = application(tmp_path)
    try:
        with patch(
            "model.logger.atomic_json", side_effect=OSError("simulated disk full")
        ):
            app.board.buttons[(6, 4)].invoke()
            app.board.buttons[(4, 4)].invoke()
            app.update()
            assert "History was not saved" in app.persist_warning.cget("text")
        app.retry_history()
        app.update()
        assert "Local profiles and match history saved" in app.persist_warning.cget(
            "text"
        )
        assert app.manager.revision == 1
    finally:
        app.destroy()


def test_real_gui_capture_quest_and_new_match_preserves_xp(tmp_path):
    from unittest.mock import patch
    from model.board import HerniPlocha
    from model.piece import Kral, Vez, Pesak

    app = application(tmp_path)
    try:
        b = HerniPlocha(False)
        for square, piece in [
            ((7, 7), Kral("white")),
            ((0, 7), Kral("black")),
            ((7, 0), Vez("white")),
            ((1, 0), Pesak("black")),
        ]:
            b.poloz(square, piece)
        app.manager.plocha = b
        app.refresh()
        app.board.buttons[(7, 0)].invoke()
        app.board.buttons[(1, 0)].invoke()
        app.update()
        assert app.manager.revision == 1
        assert app.users.uzivatele["alice"].xp == 10
        assert app.manager.quest_manager.dokoncil("alice", "capture")
        assert "10 XP" in app.white_panel.xp.cget("text")
        with patch("view.app.messagebox.askyesno", return_value=True):
            app.new_game()
        app.update()
        assert app.manager.revision == 0
        assert app.users.uzivatele["alice"].xp == 10
        assert not app.manager.quest_manager.dokoncil("alice", "capture")
    finally:
        app.destroy()
