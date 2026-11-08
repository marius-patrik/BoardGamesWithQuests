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
        pytest.skip(f'Graphical display unavailable: {exc}')
    app.users.vytvor_uzivatele('alice','Alice')
    app.users.vytvor_uzivatele('bob','Bob')
    app.show_setup()
    app.seat_choices['white'].set('alice')
    app.seat_choices['black'].set('bob')
    app.start_match()
    app.update()
    return app


def test_setup_and_button_board_move(tmp_path):
    app=application(tmp_path)
    try:
        assert len(app.board.buttons)==64
        app.board.buttons[(6,4)].invoke()
        app.update()
        assert (4,4) in app.controller.destinace
        app.board.buttons[(4,4)].invoke()
        app.update()
        assert app.manager.aktivni_barva=='black'
        assert 'e2' in app.history.get('1.0','end')
        assert app.manager.logger.path.exists()
    finally:
        app.destroy()


def test_keyboard_board_focus_and_cancel_selection(tmp_path):
    app=application(tmp_path)
    try:
        assert app.board._focus((6,4))=='break'
        app.board.buttons[(6,4)].invoke()
        app.update()
        assert app.controller.vybrane==(6,4)
        app.controller.zrus_vyber()
        assert app.controller.vybrane is None
        assert app.manager.revision==0
    finally:
        app.destroy()


def test_terminal_display(tmp_path):
    app=application(tmp_path)
    try:
        app.controller.odstup()
        app.update()
        assert app.manager.stav=='terminal'
        assert 'GAME OVER' in app.turn['text']
        assert 'disabled' in app.resign_button.state()
    finally:
        app.destroy()
