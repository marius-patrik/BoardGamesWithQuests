"""Actual Tkinter user-path acceptance under an obligatory Xvfb display."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path

import pytest

from model.game.session import DesktopSession
from view.app import build_application, open_settings


@pytest.fixture
def window(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    root = tk.Tk()
    root.geometry("1100x860")
    build_application(root, "chess", show_modal=False)
    root.update_idletasks()
    root.update()
    try:
        yield root
    finally:
        try:
            root.game_view.stop_auto_refresh()
            root.destroy()
        except tk.TclError:
            pass


def click_canvas(window, row, col):
    canvas = window.game_view.board_view.canvas
    size = window.game_view.board_view.square_size
    canvas.event_generate("<Button-1>", x=int((col + 0.5) * size), y=int((row + 0.5) * size))
    window.update()


def test_real_board_clicks_submit_authoritative_pawn_move(window):
    assert window.game_view.board_view.board.get_piece_at((6, 4)).getType() == "pawn"
    click_canvas(window, 6, 4)
    controller = window.window_controller.game_controller
    assert controller.selected_square == (6, 4)
    assert (5, 4) in controller.highlighted_moves
    click_canvas(window, 5, 4)
    state = controller.session.snapshot()
    assert state["revision"] == 1
    assert next((p for p in state["board"] if p["square"] == [6, 4]), None) is None
    assert next((p for p in state["board"] if p["square"] == [5, 4]), None)["kind"] == "pawn"
    assert window.game_view.board_view.board.get_piece_at((5, 4)).getType() == "pawn"
    assert window.game_view.history.size() == 1
    assert "→" in window.game_view.history.get(0)


def test_clicking_illegal_destination_keeps_board_and_revision(window):
    before = window.window_controller.game_controller.session.snapshot()
    click_canvas(window, 6, 4)
    click_canvas(window, 2, 4)
    assert window.window_controller.game_controller.session.snapshot() == before
    assert window.game_view.history.size() == 0


def test_preferences_dialog_saves_and_reloads_supported_non_executable_settings(window):
    dialog = open_settings(window, window.window_controller)
    dialog.size.set(64)
    dialog.coordinates.set(False)
    dialog.save()
    window.update()
    assert window.game_view.board_view.square_size == 64
    assert window.game_view.board_view.show_coordinates is False
    record = (
        Path(__import__("os").environ["XDG_CONFIG_HOME"])
        / "BoardGamesWithQuests"
        / "preferences.json"
    )
    saved = json.loads(record.read_text())
    assert saved == {"board_size": 64, "show_coordinates": False}
    next_dialog = open_settings(window, window.window_controller)
    assert next_dialog.size.get() == 64
    assert next_dialog.coordinates.get() is False
    next_dialog.close()


def test_game_switch_through_visible_new_game_modal_resets_board(window):
    window.game_view.on_new_game()
    window.update()
    from view.start_modal import StartModal

    modals = [child for child in window.winfo_children() if isinstance(child, tk.Toplevel)]
    assert modals
    selector = next(
        widget
        for widget in modals[-1].winfo_children()[0].winfo_children()
        if isinstance(widget, __import__("tkinter").ttk.Combobox)
    )
    selector.set("checkers")
    modal_start = next(
        nested
        for nested in modals[-1].winfo_children()[0].winfo_children()
        if isinstance(nested, __import__("tkinter").ttk.Frame)
    )
    start_button = next(
        widget
        for widget in modal_start.winfo_children()
        if isinstance(widget, __import__("tkinter").ttk.Button) and widget.cget("text") == "Start"
    )
    start_button.invoke()
    window.update()
    controller = window.window_controller.game_controller
    assert controller.session.game == "checkers"
    assert controller.session.snapshot()["revision"] == 0
    assert len(controller.session.snapshot()["board"]) == 24
    assert window.game_view.board_view.board.get_piece_at((7, 0)) is not None
    assert window.game_view.history.size() == 0


def test_snapshot_export_from_real_window_is_replayable(window, tmp_path, monkeypatch):
    from view import player_game_view

    click_canvas(window, 6, 4)
    click_canvas(window, 4, 4)
    destination = tmp_path / "game.json"
    # Only the OS-owned save-file selector is replaced with the chosen path.
    monkeypatch.setattr(
        player_game_view.filedialog,
        "asksaveasfilename",
        lambda **kwargs: str(destination),
    )
    window.game_view.export_game()
    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert saved["revision"] == 1
    assert DesktopSession.recover(saved).snapshot() == saved


def test_hostile_preferences_are_not_accepted_or_executed(window, tmp_path):
    from model.game.preferences import (
        PreferencesError,
        load_preferences,
        save_preferences,
    )

    base = tmp_path / "attack"
    base.mkdir()
    with pytest.raises(PreferencesError):
        save_preferences(
            {
                "board_size": 56,
                "show_coordinates": True,
                "quests": [{"python": "raise SystemExit"}],
            },
            base,
        )
    assert not list(base.iterdir())
    (base / "preferences.json").write_text(
        '{"board_size": 56, "show_coordinates": true, "rules": []}',
        encoding="utf-8",
    )
    with pytest.raises(PreferencesError):
        load_preferences(base)
    (base / "preferences.json").unlink()
    outside = tmp_path / "outside.json"
    outside.write_text("untouched", encoding="utf-8")
    (base / "preferences.json").symlink_to(outside)
    with pytest.raises(PreferencesError):
        save_preferences({"board_size": 56, "show_coordinates": True}, base)
    assert outside.read_text() == "untouched"


def test_export_and_reopen_real_game_after_switch(window, tmp_path, monkeypatch):
    from model.game.persistence import load_session
    from view import player_game_view

    click_canvas(window, 6, 4)
    click_canvas(window, 4, 4)
    previous = window.window_controller.game_controller.session.snapshot()
    saved = tmp_path / "saved.json"
    monkeypatch.setattr(
        player_game_view.filedialog, "asksaveasfilename", lambda **kwargs: str(saved)
    )
    window.game_view.export_game()
    assert load_session(saved).snapshot() == previous
    window.window_controller.game_controller.new_game("checkers")
    window.game_view.reload()
    assert window.window_controller.game_controller.session.game == "checkers"
    monkeypatch.setattr(player_game_view.filedialog, "askopenfilename", lambda **kwargs: str(saved))
    window.game_view.open_game()
    assert window.window_controller.game_controller.session.snapshot() == previous
    assert window.window_controller.game_controller.session.game == "chess"
    assert window.game_view.history.size() == 1


def test_bad_saved_game_preserves_live_window_and_reports_error(window, tmp_path, monkeypatch):
    from model.game.persistence import SessionFileError, load_session
    from view import player_game_view

    before = window.window_controller.game_controller.session.snapshot()
    bad = tmp_path / "invalid.json"
    bad.write_text('{"revision": 1, "revision": 99}', encoding="utf-8")
    monkeypatch.setattr(player_game_view.filedialog, "askopenfilename", lambda **kwargs: str(bad))
    errors = []
    monkeypatch.setattr(
        player_game_view.messagebox,
        "showerror",
        lambda _title, message, **kwargs: errors.append(str(message)),
    )
    window.game_view.open_game()
    assert errors and "duplicate" in errors[0]
    assert window.window_controller.game_controller.session.snapshot() == before
    with pytest.raises(SessionFileError):
        load_session(bad)



def test_notation_button_exports_actual_user_game_as_pgn(window, tmp_path, monkeypatch):
    from view import player_game_view
    click_canvas(window, 6, 4)
    click_canvas(window, 4, 4)
    target = tmp_path / "real-game.pgn"
    monkeypatch.setattr(
        player_game_view.filedialog, "asksaveasfilename",
        lambda **kwargs: str(target),
    )
    window.game_view.export_notation()
    assert target.exists()
    contents = target.read_text("utf-8")
    assert '[Result "*"]' in contents
    assert "1. e4 *" in contents
    assert window.window_controller.game_controller.session.snapshot()["revision"] == 1
