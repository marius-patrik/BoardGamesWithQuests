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
    selector.set("English Draughts")
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
        player_game_view.filedialog,
        "asksaveasfilename",
        lambda **kwargs: str(target),
    )
    window.game_view.export_notation()
    assert target.exists()
    contents = target.read_text("utf-8")
    assert '[Result "*"]' in contents
    assert "1. e4 *" in contents
    assert window.window_controller.game_controller.session.snapshot()["revision"] == 1


def test_resign_from_real_ui_commits_terminal_result_and_blocks_further_moves(window, monkeypatch):
    from view import player_game_view

    monkeypatch.setattr(player_game_view.messagebox, "askyesno", lambda *a, **k: True)
    window.game_view.resign_game()
    state = window.window_controller.game_controller.session.snapshot()
    assert state["outcome"]["kind"] == "win"
    assert state["outcome"]["winner"] == "black"
    assert state["revision"] == 1
    click_canvas(window, 6, 4)
    assert window.window_controller.game_controller.session.snapshot() == state
    assert DesktopSession.recover(state).snapshot() == state


def test_unavailable_draw_claim_does_not_mutate_authoritative_game(window, monkeypatch):
    from view import player_game_view

    before = window.window_controller.game_controller.session.snapshot()
    messages = []
    monkeypatch.setattr(
        player_game_view.messagebox,
        "showinfo",
        lambda *a, **k: messages.append(a),
    )
    monkeypatch.setattr(
        player_game_view.simpledialog,
        "askinteger",
        lambda *a, **k: 1,
    )
    # A rejected claim displays a blocking Tk messagebox in the real UI.
    # Capture that player-facing error instead of deadlocking the Xvfb runner.
    monkeypatch.setattr(
        player_game_view.messagebox,
        "showerror",
        lambda *a, **k: messages.append(a),
    )
    window.game_view.claim_draw()
    assert messages, "rejected claim must display a player-visible explanation"
    assert window.window_controller.game_controller.session.snapshot() == before
    assert window.window_controller.game_controller.session.snapshot()["outcome"] is None


@pytest.mark.parametrize("game", ["chess", "checkers"])
@pytest.mark.parametrize("size", [(840, 640), (1024, 768), (1100, 760), (1440, 900)])
def test_responsive_live_board_actions_and_clocks(tmp_path, monkeypatch, game, size):
    """Check actual Tk bounds and play two moves across a viewport resize."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    root = tk.Tk()
    root.geometry(f"{size[0]}x{size[1]}")
    build_application(root, game, show_modal=False)
    try:
        root.update_idletasks()
        root.update()
        view = root.game_view
        canvas = view.board_view.canvas

        def inside(widget):
            assert widget.winfo_ismapped()
            assert widget.winfo_width() > 0 and widget.winfo_height() > 0
            assert widget.winfo_rootx() >= root.winfo_rootx()
            assert widget.winfo_rooty() >= root.winfo_rooty()
            assert widget.winfo_rootx() + widget.winfo_width() <= (
                root.winfo_rootx() + root.winfo_width()
            )
            assert widget.winfo_rooty() + widget.winfo_height() <= (
                root.winfo_rooty() + root.winfo_height()
            )

        def inspect():
            assert root.winfo_width() >= 840 and root.winfo_height() >= 640
            board = view.board_view
            assert board.square_size >= 32
            assert canvas.winfo_width() >= board.board.cols * board.square_size
            assert canvas.winfo_height() >= board.board.rows * board.square_size
            for widget in (
                canvas,
                view.top_player,
                view.bottom_player,
                view.quest_viewport,
                view.history,
            ):
                inside(widget)
            for name in (
                "New game",
                "Open game",
                "Settings",
                "Quit",
                "Claim draw",
                "Resign",
                "Export",
                "Notation",
            ):
                button = view.action_buttons[name]
                inside(button)
                # Confirm all actions belong to a live Tk keyboard focus cycle.
                assert button.tk.call("tk_focusNext", button._w)

        def play_one_move():
            session = root.window_controller.game_controller.session
            actions = session.legal_actions()
            move = next(
                action
                for action in actions
                if sum(
                    a["start"] == action["start"] and a["hops"][-1] == action["hops"][-1]
                    for a in actions
                )
                == 1
            )
            click_canvas(root, *move["start"])
            assert root.window_controller.game_controller.selected_square == tuple(move["start"])
            click_canvas(root, *move["hops"][-1])

        inspect()
        before = root.window_controller.game_controller.session.snapshot()["revision"]
        play_one_move()
        assert root.window_controller.game_controller.session.snapshot()["revision"] == before + 1
        root.geometry("1100x760" if size[0] == 840 else "840x640")
        root.update_idletasks()
        root.update()
        inspect()
        play_one_move()
        assert root.window_controller.game_controller.session.snapshot()["revision"] == before + 2
    finally:
        root.game_view.stop_auto_refresh()
        root.destroy()


def test_responsive_preferences_keep_saved_size_without_cropping(window):
    view = window.game_view
    window.geometry("840x640")
    window.update()
    view.apply_preferences({"board_size": 88, "show_coordinates": True})
    window.update()
    assert view._preferred_board_size == 88
    assert 32 <= view.board_view.square_size < 88
    compact_size = view.board_view.square_size
    window.geometry("1440x900")
    window.update()
    assert compact_size < view.board_view.square_size <= 88
    assert view.board_view.canvas.winfo_width() == 8 * view.board_view.square_size


# #451: the widgets below run with the real bundled game engine under Xvfb.
# Only OS-owned file/dialog responses are scripted; game state and legal moves are not mocked.
def _play_one_legal_move(window):
    session = window.window_controller.game_controller.session
    actions = session.legal_actions()
    move = next(
        action
        for action in actions
        if sum(
            item["start"] == action["start"] and item["hops"][-1] == action["hops"][-1]
            for item in actions
        )
        == 1
    )
    click_canvas(window, *move["start"])
    click_canvas(window, *move["hops"][-1])


def _game_chooser(window):
    return next(child for child in window.winfo_children() if isinstance(child, tk.Toplevel))


@pytest.mark.parametrize("game", ["chess", "checkers"])
def test_terminal_result_and_postgame_actions_are_authoritative(window, game, monkeypatch):
    if game != "chess":
        window.window_controller.game_controller.new_game(game)
        window.game_view.reload(clean=True)
    _play_one_legal_move(window)
    before = window.window_controller.game_controller.session.snapshot()
    expected_winner = before["participants"][str(-before["active_side"])]
    monkeypatch.setattr("view.player_game_view.messagebox.askyesno", lambda *a, **k: True)
    window.game_view.resign_game()
    window.update()
    state = window.window_controller.game_controller.session.snapshot()
    assert state["outcome"]["kind"] == "win"
    assert state["outcome"]["winner"] == expected_winner
    assert "wins" in window.game_view.turn.get()
    assert "resignation" in window.game_view.turn.get()
    assert "to move" not in window.game_view.turn.get()
    assert window.game_view.action_buttons["Resign"].instate(["disabled"])
    assert window.game_view.action_buttons["Claim draw"].instate(["disabled"])
    for label in ("New game", "Open game", "Export", "Notation"):
        assert not window.game_view.action_buttons[label].instate(["disabled"])
    click_canvas(window, 6, 4)
    assert window.window_controller.game_controller.session.snapshot() == state
    assert window.window_controller.game_controller.selected_square is None
    assert window.game_view.turn.get().startswith(
        "Chess" if game == "chess" else "English Draughts"
    )


def test_new_game_cancel_and_discard_preserve_until_choice(window, monkeypatch):
    _play_one_legal_move(window)
    before = window.window_controller.game_controller.session.snapshot()
    title = window.title()
    answers = iter((None, False, False))
    monkeypatch.setattr(
        "view.player_game_view.messagebox.askyesnocancel", lambda *a, **k: next(answers)
    )
    window.game_view.on_new_game()
    assert window.window_controller.game_controller.session.snapshot() == before
    assert window.title() == title
    assert not any(isinstance(child, tk.Toplevel) for child in window.winfo_children())
    window.game_view.on_new_game()
    window.update()
    modal = _game_chooser(window)
    modal_obj = next(
        widget
        for widget in modal.winfo_children()[0].winfo_children()
        if isinstance(widget, __import__("tkinter").ttk.Combobox)
    )
    assert set(modal_obj.cget("values")) == {"Chess", "English Draughts"}
    assert modal_obj.get() == "Chess"
    modal_obj.set("English Draughts")
    start = next(
        widget
        for frame in modal.winfo_children()[0].winfo_children()
        if isinstance(frame, __import__("tkinter").ttk.Frame)
        for widget in frame.winfo_children()
        if isinstance(widget, __import__("tkinter").ttk.Button) and widget.cget("text") == "Start"
    )
    # Closing the chooser after selecting Discard must NOT discard the running session.
    # Close using the actual Cancel button instead of mutating the game controller.
    cancel = next(
        widget
        for widget in modal.winfo_children()[0].winfo_children()
        if isinstance(widget, __import__("tkinter").ttk.Button) and widget.cget("text") == "Cancel"
    )
    cancel.invoke()
    window.update()
    assert window.window_controller.game_controller.session.snapshot() == before
    assert window.title() == title
    # A new choice after Discard really starts the selected bundled game.
    window.game_view.on_new_game()
    window.update()
    chooser = _game_chooser(window)
    body = chooser.winfo_children()[0]
    select = next(
        w for w in body.winfo_children() if isinstance(w, __import__("tkinter").ttk.Combobox)
    )
    select.set("English Draughts")
    start = next(
        w
        for frame in body.winfo_children()
        if isinstance(frame, __import__("tkinter").ttk.Frame)
        for w in frame.winfo_children()
        if isinstance(w, __import__("tkinter").ttk.Button) and w.cget("text") == "Start"
    )
    start.invoke()
    window.update()
    assert window.window_controller.game_controller.session.game == "checkers"
    assert window.window_controller.game_controller.session.snapshot()["revision"] == 0
    assert window.title().endswith("English Draughts")
    assert not window.game_view._has_unsaved_progress()


def test_open_cancel_and_failed_replay_preserve_session_title_and_revision(
    window, tmp_path, monkeypatch
):
    from view import player_game_view

    _play_one_legal_move(window)
    previous = window.window_controller.game_controller.session.snapshot()
    title = window.title()
    bad = tmp_path / "invalid.json"
    bad.write_text('{"revision": 1, "revision": 4}', encoding="utf-8")
    answers = iter((None, False, False))
    monkeypatch.setattr(
        player_game_view.messagebox, "askyesnocancel", lambda *a, **k: next(answers)
    )
    filepaths = iter((str(bad), ""))
    monkeypatch.setattr(
        player_game_view.filedialog, "askopenfilename", lambda **kwargs: next(filepaths)
    )
    errors = []
    monkeypatch.setattr(
        player_game_view.messagebox,
        "showerror",
        lambda _title, message, **kwargs: errors.append(message),
    )
    window.game_view.open_game()  # initial Cancel, file chooser must not open
    assert window.window_controller.game_controller.session.snapshot() == previous
    assert window.title() == title
    window.game_view.open_game()  # Discard, but malformed input must preserve game
    assert errors and "duplicate" in errors[-1]
    assert window.window_controller.game_controller.session.snapshot() == previous
    assert window.title() == title
    window.game_view.open_game()  # Discard, file chooser Cancel
    assert window.window_controller.game_controller.session.snapshot() == previous
    assert window.title() == title


def test_save_then_open_switches_title_and_retains_replay(window, tmp_path, monkeypatch):
    from view import player_game_view
    from model.game.persistence import load_session, save_session

    _play_one_legal_move(window)
    old = window.window_controller.game_controller.session.snapshot()
    chess_save = tmp_path / "chess.json"
    save_session(window.window_controller.game_controller.session, chess_save)
    window.window_controller.game_controller.new_game("checkers")
    window.game_view.reload(clean=True)
    _play_one_legal_move(window)
    checkers = window.window_controller.game_controller.session.snapshot()
    save_before_open = tmp_path / "checkers.json"
    monkeypatch.setattr(player_game_view.messagebox, "askyesnocancel", lambda *a, **k: True)
    monkeypatch.setattr(
        player_game_view.filedialog,
        "asksaveasfilename",
        lambda **k: str(save_before_open),
    )
    monkeypatch.setattr(player_game_view.filedialog, "askopenfilename", lambda **k: str(chess_save))
    window.game_view.open_game()
    window.update()
    assert load_session(save_before_open).snapshot() == checkers
    assert window.window_controller.game_controller.session.snapshot() == old
    assert window.title().endswith("Chess")
    assert not window.game_view._has_unsaved_progress()
    assert window.game_view.history.size() == 1


def test_save_cancel_and_io_error_abort_destructive_new_game(window, tmp_path, monkeypatch):
    from view import player_game_view

    _play_one_legal_move(window)
    original = window.window_controller.game_controller.session.snapshot()
    title = window.title()
    monkeypatch.setattr(player_game_view.messagebox, "askyesnocancel", lambda *a, **k: True)
    monkeypatch.setattr(player_game_view.filedialog, "asksaveasfilename", lambda **k: "")
    window.game_view.on_new_game()
    assert window.window_controller.game_controller.session.snapshot() == original
    assert window.title() == title
    errors = []
    monkeypatch.setattr(
        player_game_view.messagebox,
        "showerror",
        lambda _title, msg, **kwargs: errors.append(msg),
    )
    monkeypatch.setattr(
        player_game_view.filedialog,
        "asksaveasfilename",
        lambda **k: str(tmp_path / "no-such-directory" / "bad.json"),
    )
    window.game_view.on_new_game()
    assert errors
    assert window.window_controller.game_controller.session.snapshot() == original
    assert window.title() == title


def test_claim_prompt_has_real_newlines_and_game_validates_claim(window, monkeypatch):
    from view import player_game_view

    prompts = []
    messages = []
    monkeypatch.setattr(
        player_game_view.simpledialog,
        "askinteger",
        lambda title, prompt, **kwargs: prompts.append(prompt) or 1,
    )
    monkeypatch.setattr(
        player_game_view.messagebox,
        "showerror",
        lambda title, message, **kwargs: messages.append(message),
    )
    prior = window.window_controller.game_controller.session.snapshot()
    window.game_view.claim_draw()
    assert prompts and "\n1." in prompts[0] and "\\n" not in prompts[0]
    assert "threefold repetition" in prompts[0]
    assert messages and "not available" in messages[0]
    assert window.window_controller.game_controller.session.snapshot() == prior
    window.window_controller.game_controller.new_game("checkers")
    window.game_view.reload(clean=True)
    assert window.game_view.action_buttons["Claim draw"].instate(["disabled"])


def test_postgame_save_feedback_survives_periodic_refresh(window, tmp_path, monkeypatch):
    from view import player_game_view
    from model.game.persistence import load_session

    monkeypatch.setattr(player_game_view.messagebox, "askyesno", lambda *args, **kwargs: True)
    window.game_view.resign_game()
    state = window.window_controller.game_controller.session.snapshot()
    target = tmp_path / "final-game.json"
    monkeypatch.setattr(
        player_game_view.filedialog, "asksaveasfilename", lambda **kwargs: str(target)
    )
    assert window.game_view.export_game() is True
    window.game_view.refresh()  # same periodic refresh path as the running Tk clock
    assert "Saved game" in window.game_view.status.get()
    assert target.name in window.game_view.status.get()
    assert load_session(target).snapshot() == state
    assert "wins" in window.game_view.turn.get()
    assert window.game_view.action_buttons["Resign"].instate(["disabled"])
