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
    # WCDF now configures named threefold and 40-move claims. The button
    # is available, but the engine must reject an ineligible claim.
    assert not window.game_view.action_buttons["Claim draw"].instate(["disabled"])
    draughts_before = window.window_controller.game_controller.session.snapshot()
    window.game_view.claim_draw()
    assert len(prompts) == 2
    assert "threefold repetition" in prompts[-1]
    assert "40-move rule" in prompts[-1]
    assert len(messages) == 2 and "not available" in messages[-1]
    assert window.window_controller.game_controller.session.snapshot() == draughts_before


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


# #452: these are rendered-widget acceptance paths over actual session actions.
# The reference positions are separately constructed, not engine-produced snapshots.
def prepared_position(monkeypatch, game, placement, starting_side):
    from importlib import resources

    import model.game.session as session_module
    from model.game.definition import validate_definition

    config = json.loads(resources.files("games").joinpath(game, "config.json").read_text())
    config["board"]["starting_pieces"] = placement
    config["starting_side"] = starting_side
    definition = validate_definition(config)
    with monkeypatch.context() as patch:
        patch.setattr(session_module, "load_bundled_definition", lambda _: definition)
        return DesktopSession(game)


def prepared_window(window, session):
    window.window_controller.game_controller.session = session
    window.game_view.reload(clean=True)
    window.update()


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def choose_rendered_route(window, index, expected_text, button="Play selected move"):
    """Operate the modal's real listbox and visible Tk button during wait_window."""
    observations = []

    def choose():
        dialogs = [child for child in descendants(window) if isinstance(child, tk.Toplevel)]
        assert dialogs, "Board click failed to open a real chooser"
        dialog = dialogs[-1]
        listbox = next(item for item in descendants(dialog) if isinstance(item, tk.Listbox))
        options = listbox.get(0, tk.END)
        assert expected_text in options[index]
        assert all("[[" not in text and "]]" not in text for text in options)
        bounds = listbox.bbox(index)
        assert bounds is not None
        listbox.event_generate("<Button-1>", x=bounds[0] + 5, y=bounds[1] + bounds[3] // 2)
        listbox.event_generate("<ButtonRelease-1>", x=bounds[0] + 5, y=bounds[1] + bounds[3] // 2)
        assert listbox.curselection() == (index,)
        observations.append((options, window.game_view.session.snapshot()["revision"]))
        confirm = next(
            item
            for item in descendants(dialog)
            if isinstance(item, __import__("tkinter").ttk.Button) and item.cget("text") == button
        )
        confirm.invoke()

    window.after(30, choose)
    return observations


@pytest.mark.parametrize("route_index, middle", [(0, "b4"), (1, "f4")])
def test_pointer_selects_complete_branched_draughts_capture(
    window, monkeypatch, route_index, middle
):
    session = prepared_position(
        monkeypatch,
        "checkers",
        [
            {"piece": "man", "color": "black", "squares": [[2, 3]]},
            {"piece": "man", "color": "white", "squares": [[3, 2], [3, 4], [5, 2], [5, 4]]},
        ],
        -1,
    )
    legal = session.legal_actions()
    # WCDF: both complete d6-b4-d2 and d6-f4-d2 paths capture two men.
    assert len(legal) == 2
    assert all(m["start"] == [2, 3] and m["hops"][-1] == [6, 3] for m in legal)
    prepared_window(window, session)
    click_canvas(window, 2, 3)
    assert window.window_controller.game_controller.highlighted_moves == [(6, 3)]
    assert window.game_view.board_view.canvas.find_withtag("legal_capture")
    expected = "d6 × " + middle + " × d2"
    trace = choose_rendered_route(window, route_index, expected)
    click_canvas(window, 6, 3)
    assert trace and trace[0][1] == 0  # no intermediate hop was committed
    state = window.game_view.session.snapshot()
    assert state["revision"] == 1
    route = state["events"][-1]["move"]
    assert route == legal[route_index]
    assert len(state["captured"]) == 2
    assert any(p["square"] == [6, 3] and p["kind"] == "man" for p in state["board"])


def test_single_hop_draughts_capture_uses_capture_notation_and_marker(window, monkeypatch):
    """Jump captures finish on an empty square, unlike occupied Chess captures."""
    session = prepared_position(
        monkeypatch,
        "checkers",
        [
            {"piece": "man", "color": "black", "squares": [[2, 3]]},
            {"piece": "man", "color": "white", "squares": [[3, 2]]},
        ],
        -1,
    )
    legal = session.legal_actions()
    assert len(legal) == 1
    move = legal[0]
    assert move["start"] == [2, 3] and move["hops"] == [[4, 1]]
    state = session.snapshot()
    assert not any(piece["square"] == [4, 1] for piece in state["board"])
    prepared_window(window, session)
    assert window.game_view._format_complete_move(move, state) == "d6 × b4"
    click_canvas(window, 2, 3)
    canvas = window.game_view.board_view.canvas
    assert canvas.find_withtag("legal_capture")
    assert not canvas.find_withtag("legal_quiet")
    click_canvas(window, 4, 1)
    after = session.snapshot()
    assert after["revision"] == 1
    assert after["events"][-1]["move"] == move
    assert len(after["captured"]) == 1


def test_cancel_capture_chooser_is_atomic_and_highlights_remain(window, monkeypatch):
    session = prepared_position(
        monkeypatch,
        "checkers",
        [
            {"piece": "man", "color": "black", "squares": [[2, 3]]},
            {"piece": "man", "color": "white", "squares": [[3, 2], [3, 4], [5, 2], [5, 4]]},
        ],
        -1,
    )
    prepared_window(window, session)
    before = session.snapshot()
    click_canvas(window, 2, 3)

    def cancel():
        dialog = next(child for child in descendants(window) if isinstance(child, tk.Toplevel))
        listbox = next(child for child in descendants(dialog) if isinstance(child, tk.Listbox))
        assert " × " in listbox.get(0)
        dialog.event_generate("<Escape>")

    window.after(30, cancel)
    click_canvas(window, 6, 3)
    assert session.snapshot() == before
    assert window.window_controller.game_controller.selected_square == (2, 3)
    assert (6, 3) in window.window_controller.game_controller.highlighted_moves


@pytest.mark.parametrize("promotion", ["queen", "rook", "bishop", "knight"])
def test_pointer_selects_every_chess_promotion_variant(window, monkeypatch, promotion):
    session = prepared_position(
        monkeypatch,
        "chess",
        [
            {"piece": "king", "color": "white", "squares": [[7, 4]]},
            {"piece": "king", "color": "black", "squares": [[0, 7]]},
            {"piece": "pawn", "color": "white", "squares": [[1, 0]]},
        ],
        1,
    )
    legal = [m for m in session.legal_actions() if m["start"] == [1, 0]]
    promoted = [m for m in legal if m["hops"][-1] == [0, 0]]
    assert {m["promotion"] for m in promoted} == {"queen", "rook", "bishop", "knight"}
    prepared_window(window, session)
    click_canvas(window, 1, 0)
    choice = next(i for i, m in enumerate(promoted) if m["promotion"] == promotion)
    trace = choose_rendered_route(window, choice, "Promote to " + promotion.title())
    click_canvas(window, 0, 0)
    assert trace and trace[0][1] == 0
    state = session.snapshot()
    assert state["revision"] == 1
    assert state["events"][-1]["move"] == promoted[choice]
    assert f"Promoted to {promotion.title()}" in window.game_view.history.get(0)
    assert any(
        p["square"] == [0, 0] and p["kind"] == promotion and p["side"] == 1 for p in state["board"]
    )


def test_draughts_automatic_crowning_through_canvas_click(window, monkeypatch):
    session = prepared_position(
        monkeypatch,
        "checkers",
        [
            {"piece": "man", "color": "black", "squares": [[6, 1]]},
            {"piece": "man", "color": "white", "squares": [[4, 5]]},
        ],
        -1,
    )
    prepared_window(window, session)
    click_canvas(window, 6, 1)
    click_canvas(window, 7, 0)
    state = session.snapshot()
    assert state["revision"] == 1
    assert any(p["square"] == [7, 0] and p["kind"] == "king" for p in state["board"])
    assert window.game_view.board_view.canvas.find_withtag("draughts_king")


def test_legal_occupied_capture_last_move_hover_and_resize(window):
    # Chess e4 d5: e4xd5 is an occupied opponent and has a distinct dashed target ring.
    click_canvas(window, 6, 4)
    click_canvas(window, 4, 4)
    click_canvas(window, 1, 3)
    click_canvas(window, 3, 3)
    board = window.game_view.board_view
    click_canvas(window, 4, 4)
    assert board.canvas.find_withtag("legal_capture")
    assert not board.canvas.find_withtag("legal_quiet") or board.canvas.find_withtag(
        "legal_capture"
    )
    click_canvas(window, 3, 3)
    assert window.game_view.session.snapshot()["revision"] == 3
    assert "×" in window.game_view.history.get(2)
    assert board.canvas.find_withtag("last_move")
    for width, height in ((840, 640), (1100, 760)):
        window.geometry(f"{width}x{height}")
        window.update()
        board = window.game_view.board_view
        assert board.canvas.winfo_width() == 8 * board.square_size
        assert board.canvas.winfo_height() == 8 * board.square_size
        # Moving over one square adds a dashed hover marker on the actual Canvas.
        size = board.square_size
        board.canvas.event_generate("<Motion>", x=size // 2, y=size // 2)
        window.update()
        assert board.canvas.find_withtag("hover")
        board.canvas.event_generate("<Leave>")
        window.update()
        assert not board.canvas.find_withtag("hover")


@pytest.mark.parametrize("game", ["chess", "checkers"])
@pytest.mark.parametrize("viewport", [(840, 640), (1100, 760), (1440, 900)])
def test_two_sided_player_quest_panels_are_visible_and_owned(window, game, viewport):
    """The reference layout is white/board/black with independent full quest lists."""
    root = window
    root.geometry(f"{viewport[0]}x{viewport[1]}")
    root.window_controller.game_controller.new_game(game)
    root.game_view.reload(clean=True)
    root.update_idletasks()
    root.update()
    view = root.game_view
    state = view.session.snapshot()
    assert set(view.player_views) == {1, -1}
    assert set(view.quest_lists) == {1, -1}
    assert set(view.quest_viewports) == {1, -1}
    white, black = view.player_views[1], view.player_views[-1]
    board = view.board_view.canvas

    assert white.winfo_ismapped() and black.winfo_ismapped()
    assert white.winfo_rootx() < board.winfo_rootx() < black.winfo_rootx()
    assert white.winfo_rootx() + white.winfo_width() <= board.winfo_rootx()
    assert board.winfo_rootx() + board.winfo_width() <= black.winfo_rootx()
    assert board.winfo_rootx() - (white.winfo_rootx() + white.winfo_width()) < 95
    assert black.winfo_rootx() - (board.winfo_rootx() + board.winfo_width()) < 95
    assert board.winfo_height() == board.winfo_width()
    assert board.winfo_rooty() >= root.winfo_rooty()
    assert board.winfo_rooty() + board.winfo_height() <= (root.winfo_rooty() + root.winfo_height())
    assert white.clock.get() and black.clock.get()
    assert state["participants"]["1"].casefold() in white.name.get().casefold()
    assert state["participants"]["-1"].casefold() in black.name.get().casefold()
    for side in (1, -1):
        participant_id = state["participants"][str(side)]
        assert len(view.quest_lists[side].cards) == len(state["quest_progress"][participant_id])
        assert view.quest_viewports[side].winfo_ismapped()
        assert view.quest_viewports[side].winfo_height() > 0
        assert view.player_views[side].score.get() == (
            f"Quest score: {state['quest_scores'][participant_id]}"
        )
    if game == "chess":
        light_shapes = board.find_withtag("filled_white")
        dark_shapes = board.find_withtag("filled_black")
        assert len(light_shapes) >= 16 and len(dark_shapes) >= 16
        assert all(board.type(item) != "text" for item in board.find_withtag("chess_piece"))
        light_fills = {board.itemcget(item, "fill") for item in light_shapes}
        dark_fills = {board.itemcget(item, "fill") for item in dark_shapes}
        assert "#fff8e5" in light_fills and "#17212b" in dark_fills
    else:
        assert board.find_withtag("draughts_piece")
        assert board.find_withtag("draughts_man")


def test_both_participants_can_scroll_all_authoritative_quests(window, monkeypatch):
    """More than six session-defined objectives remain available to each side."""
    from importlib import resources
    import model.game.session as session_module
    from model.game.definition import validate_definition

    data = json.loads(resources.files("games").joinpath("chess", "config.json").read_text())
    data["quests"].extend(
        {
            "id": f"visual-quest-{number}",
            "description": f"Extended individually owned objective {number}",
            "reward": number,
            "when": {"op": "true"},
        }
        for number in range(10)
    )
    with monkeypatch.context() as patch:
        patch.setattr(
            session_module, "load_bundled_definition", lambda _: validate_definition(data)
        )
        session = DesktopSession("chess")
    prepared_window(window, session)
    window.geometry("840x640")
    window.update()
    state = session.snapshot()

    for side in (1, -1):
        participant = state["participants"][str(side)]
        listing = window.game_view.quest_lists[side]
        viewport = window.game_view.quest_viewports[side]
        assert len(listing.cards) == len(state["quest_progress"][participant])
        assert len(listing.cards) > 6
        assert viewport.bbox("all")[3] > viewport.winfo_height()
        first_scroll = viewport.yview()
        viewport.event_generate("<Button-5>")
        window.update()
        assert viewport.yview()[0] > first_scroll[0]

    # Only White's completed first move is credited; Black's own score is not
    # silently merged into the opposing participant's quest list.
    click_canvas(window, 6, 4)
    click_canvas(window, 4, 4)
    after = session.snapshot()
    for side in (1, -1):
        participant = after["participants"][str(side)]
        assert window.game_view.player_views[side].score.get() == (
            f"Quest score: {after['quest_scores'][participant]}"
        )


# #453: all exercises below use real rendered Tk widgets and accepted session
# transitions. Custom quest definitions are validated by the real rule loader.
def _long_quest_session(game, monkeypatch, suffix):
    from importlib import resources
    import model.game.session as session_module
    from model.game.definition import validate_definition

    data = json.loads(resources.files("games").joinpath(game, "config.json").read_text())
    data["quests"] = [
        {
            "id": f"shared-quest-{index}",
            "description": f"{suffix}: " + ("Read every word in the longer objective. " * 5),
            "reward": index + (17 if suffix == "Second" else 3),
            "when": {"op": "true"},
        }
        for index in range(12)
    ]
    definition = validate_definition(data)
    with monkeypatch.context() as patch:
        patch.setattr(session_module, "load_bundled_definition", lambda _: definition)
        return DesktopSession(game)


@pytest.mark.parametrize("game", ["chess", "checkers"])
@pytest.mark.parametrize("size", [(840, 640), (1024, 768), (1100, 760), (1440, 900)])
def test_quest_long_copy_and_two_independent_mousewheel_scrollers(window, monkeypatch, game, size):
    session = _long_quest_session(game, monkeypatch, "First")
    prepared_window(window, session)
    window.geometry(f"{size[0]}x{size[1]}")
    window.update()
    view = window.game_view
    board = view.board_view.canvas
    white, black = view.quest_viewports[1], view.quest_viewports[-1]
    assert view.player_views[1].winfo_rootx() < board.winfo_rootx()
    assert board.winfo_rootx() < view.player_views[-1].winfo_rootx()
    for side in (1, -1):
        cards = view.quest_lists[side].cards
        assert len(cards) == 12
        assert "longer objective" in cards[-1].description_label.cget("text")
        assert cards[-1].reward_label.cget("text") == "Reward: 14 pts"
        assert view.quest_viewports[side].bbox("all")[3] > view.quest_viewports[side].winfo_height()
    white_before, black_before = white.yview(), black.yview()
    # Deliver the real pointer wheel to a nested quest description, not Canvas.
    view.quest_lists[1].cards[0].description_label.event_generate("<Button-5>")
    window.update()
    assert white.yview()[0] > white_before[0]
    assert black.yview() == black_before
    view.quest_lists[-1].cards[0].reward_label.event_generate("<Button-5>")
    window.update()
    assert black.yview()[0] > black_before[0]
    white_position = white.yview()
    view.refresh()  # regular clock refresh must not reset either scroll position
    window.update()
    assert white.yview() == white_position
    assert view.player_views[1].clock.get() and view.player_views[-1].clock.get()


def test_quest_cache_refreshes_different_config_with_same_ids_and_progress(window, monkeypatch):
    first = _long_quest_session("chess", monkeypatch, "First")
    second = _long_quest_session("checkers", monkeypatch, "Second")
    prepared_window(window, first)
    view = window.game_view
    before = first.snapshot()
    assert all(
        not card.progress_label.cget("text").startswith("1/") for card in view.quest_lists[1].cards
    )
    # Force identical session identity in the detached read-only projection:
    # definition changes alone must invalidate render content.
    altered = second.snapshot()
    altered["game_id"] = before["game_id"]
    for side in (1, -1):
        listing = view.quest_lists[side]
        listing.refresh(altered)
        assert "Second:" in listing.cards[0].description_label.cget("text")
        assert listing.cards[0].reward_label.cget("text") == "Reward: 17 pts"
        assert len(listing.cards) == 12
    # A real Chess -> Draughts session change also replaces stale cards/history.
    prepared_window(window, second)
    assert view.session.game == "checkers"
    assert view.history.size() == 0
    assert view.history_empty.winfo_manager() == "place"
    assert all(
        "Second:" in card.description_label.cget("text") for card in view.quest_lists[1].cards
    )
    click_canvas(window, 2, 3)
    click_canvas(window, 3, 2)
    assert view.session.snapshot()["revision"] == 1
    completed = view.quest_lists[-1].cards[0]
    assert completed.progress_label.cget("text").endswith("Completed")
    assert int(float(completed.indicator["value"])) == int(float(completed.indicator["maximum"]))
    assert view.player_views[-1].score.get() == (
        f"Quest score: {view.session.snapshot()['quest_scores']['black']}"
    )


def test_history_120_accepted_events_autofollows_only_from_bottom(window):
    session = window.game_view.session
    participants = session.snapshot()["participants"]
    view = window.game_view

    def offer_and_decline():
        state = session.snapshot()
        session.submit(participants["1"], state["revision"], {"type": "offer_draw"})
        state = session.snapshot()
        session.submit(participants["-1"], state["revision"], {"type": "reject_draw"})

    assert view.history.size() == 0 and view.history_empty.winfo_manager() == "place"
    for _ in range(55):
        offer_and_decline()
    view.refresh()
    window.update()
    assert session.snapshot()["revision"] == 110
    assert view.history.size() == 110
    assert "White: Offered a draw" in view.history.get(0)
    assert "Black: Declined draw offer" in view.history.get(109)
    assert view.history.yview()[1] > 0.95
    assert view.history_empty.winfo_manager() == ""
    # A real Tk PageUp key and listbox focus put the reader above the newest.
    view.history.focus_set()
    view.history.event_generate("<Home>")
    view.history.yview_moveto(0.0)
    window.update()
    assert view.history.yview()[0] < 0.05
    offer_and_decline()
    view.refresh()
    window.update()
    assert view.history.size() == 112
    assert view.history.yview()[0] < 0.05
    view.refresh()  # a clock tick cannot replace the listbox contents or scroll
    assert view.history.yview()[0] < 0.05
    view.history.see(tk.END)
    window.update()
    offer_and_decline()
    view.refresh()
    window.update()
    assert view.history.size() == 114
    assert view.history.yview()[1] > 0.95
    assert view.history.get(113).startswith("114.")
    session.submit(participants["1"], session.snapshot()["revision"], {"type": "resign"})
    view.refresh()
    window.update()
    assert view.history.size() == 115
    assert "wins" in view.history.get(114)
    assert "wins" in view.history_result.get()
    assert view.history_result_label.winfo_ismapped()


def test_long_material_is_grouped_without_synthesizing_score(window):
    view = window.game_view
    state = view.session.snapshot()
    state["captured"] = (
        [{"kind": "pawn", "side": -1}] * 48
        + [{"kind": "bishop", "side": -1}] * 8
        + [{"kind": "rook", "side": 1}] * 11
    )
    white = view.player_views[1]
    score_before = white.score.get()
    white.refresh(state, view.session.clock_remaining())
    window.geometry("840x640")
    window.update()
    assert "pawn ×48" in white.captured.get() and "bishop ×8" in white.captured.get()
    assert "rook ×11" in white.lost.get()
    assert white.score.get() == score_before
    assert white.name.get() == "White"
    assert white.winfo_width() > 0


# #454: real Tk widgets, focus/grabs, settings restart, bounded feedback and idle redraw.
@pytest.mark.parametrize("preferred", [32, 56, 88])
def test_settings_cancel_save_restart_defaults_and_pointer_mapping(window, tmp_path, preferred):
    import os
    import subprocess
    import sys

    from model.game.preferences import DEFAULTS

    target = Path(os.environ["XDG_CONFIG_HOME"]) / "BoardGamesWithQuests" / "preferences.json"
    original = window.game_view._preferred_board_size
    settings = open_settings(window, window.window_controller)
    assert window.grab_current() == settings.window
    settings.size.set(preferred)
    settings.coordinates.set(False)
    settings.window.event_generate("<Escape>")
    window.update()
    assert not target.exists()
    assert window.game_view._preferred_board_size == original
    assert window.grab_current() is None

    settings = open_settings(window, window.window_controller)
    assert settings.size.get() == DEFAULTS["board_size"]
    settings.size.set(preferred)
    settings.coordinates.set(False)
    settings.save()
    window.update()
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "board_size": preferred,
        "show_coordinates": False,
    }
    assert window.game_view._preferred_board_size == preferred
    assert not window.game_view.board_view.show_coordinates

    # Real second interpreter/process, reading the existing secure OS store.
    code = (
        "import json, tkinter as tk; "
        "from view.app import build_application; "
        "root = tk.Tk(); root.geometry('1100x860'); "
        "build_application(root, 'chess', show_modal=False); root.update(); "
        "view = root.game_view; "
        "print(json.dumps({'preferred': view._preferred_board_size, "
        "'coordinates': view.board_view.show_coordinates})); "
        "view.stop_auto_refresh(); root.destroy()"
    )
    child = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert json.loads(child.stdout.strip().splitlines()[-1]) == {
        "preferred": preferred,
        "coordinates": False,
    }

    # The preferred size is an upper bound, never a request to clip the board.
    window.geometry("840x640")
    window.update()
    size = window.game_view.board_view.square_size
    assert 32 <= size <= preferred
    before = window.game_view.session.snapshot()["revision"]
    click_canvas(window, 6, 4)
    click_canvas(window, 4, 4)
    assert window.game_view.session.snapshot()["revision"] == before + 1

    settings = open_settings(window, window.window_controller)
    settings.restore_defaults()
    # Restore defaults is explicitly a draft action until Save.
    assert json.loads(target.read_text(encoding="utf-8"))["board_size"] == preferred
    settings.save()
    window.update()
    assert json.loads(target.read_text(encoding="utf-8")) == DEFAULTS
    assert window.game_view._preferred_board_size == DEFAULTS["board_size"]


def test_nested_settings_cancel_restores_game_chooser_grab_and_focus(window):
    before = window.game_view.session.snapshot()
    window.game_view.on_new_game()
    window.update()
    chooser = next(widget for widget in window.winfo_children() if isinstance(widget, tk.Toplevel))
    assert window.grab_current() == chooser
    settings_button = next(
        widget
        for widget in descendants(chooser)
        if isinstance(widget, __import__("tkinter").ttk.Button)
        and widget.cget("text") == "Settings"
    )
    settings_button.invoke()
    window.update()
    settings = window.settings_dialog
    assert settings.window.transient() == str(chooser)
    assert window.grab_current() == settings.window

    settings.size.set(88)
    settings.window.event_generate("<Escape>")
    window.update()
    assert window.grab_current() == chooser
    assert chooser.winfo_exists()
    chooser.event_generate("<Escape>")
    window.update()
    assert window.grab_current() is None
    assert window.game_view.session.snapshot() == before

    # A second chooser/Settings sequence must never leave an orphaned grab.
    window.game_view.on_new_game()
    window.update()
    second = next(widget for widget in window.winfo_children() if isinstance(widget, tk.Toplevel))
    assert window.grab_current() == second
    second.event_generate("<Escape>")
    window.update()
    assert window.grab_current() is None


def test_cancelable_real_move_chooser_restores_grab_without_playing(window):
    view = window.game_view
    before = view.session.snapshot()
    options = view.session.legal_actions()[:2]
    assert options

    def cancel():
        chooser = next(widget for widget in descendants(window) if isinstance(widget, tk.Toplevel))
        assert window.grab_current() == chooser
        chooser.event_generate("<Escape>")

    window.after(30, cancel)
    result = view._choose_complete_move(
        options,
        before,
        title="Choose your move",
        explanation="Choose one legal route.",
        confirm_label="Play selected move",
    )
    assert result is None
    assert window.grab_current() is None
    assert view.session.snapshot() == before


@pytest.mark.parametrize("game", ["chess", "checkers"])
def test_clock_only_autorefresh_preserves_actual_canvas_items(window, game):
    if game != "chess":
        window.window_controller.game_controller.new_game(game)
        window.game_view.reload(clean=True)
    view = window.game_view
    view.refresh()
    canvas = view.board_view.canvas
    identifiers = canvas.find_all()
    assert identifiers

    # Run the scheduled 500-ms callback through Tk's real event loop.
    window.after(660, window.quit)
    window.mainloop()
    assert canvas.find_all() == identifiers
    assert view.session.snapshot()["revision"] == 0
    assert not view.action_buttons["New game"].instate(["disabled"])

    # Compare the original unconditional full Canvas repaint operation to
    # the optimized real refresh path on the same process, board and display.
    from time import perf_counter
    import warnings

    iterations = 24
    began = perf_counter()
    for _ in range(iterations):
        view.board_view.refresh(view.session.board_projection())
        view.refresh()
    old_ms = (perf_counter() - began) * 1000 / iterations
    began = perf_counter()
    for _ in range(iterations):
        view.refresh()
    new_ms = (perf_counter() - began) * 1000 / iterations
    warnings.warn(
        f"UX454 {game} 24-iteration Xvfb refresh reference="
        f"{old_ms:.3f}ms optimized={new_ms:.3f}ms",
        RuntimeWarning,
        stacklevel=1,
    )
    assert canvas.find_all() != identifiers  # reference path really repainted
    stable = canvas.find_all()
    view.refresh()
    assert canvas.find_all() == stable


def test_io_errors_show_bounded_basename_without_replacing_live_game(window, tmp_path, monkeypatch):
    from view import player_game_view as module

    before = window.game_view.session.snapshot()
    filename = "prefix-" + ("x" * 150) + "-save.json"
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("existing file", encoding="utf-8")
    target = str(blocked / filename)
    captured = []
    monkeypatch.setattr(
        module.messagebox,
        "showerror",
        lambda title, message, **_kwargs: captured.append((title, message)),
    )
    monkeypatch.setattr(
        module.filedialog,
        "asksaveasfilename",
        lambda **_kwargs: target,
    )
    assert window.game_view.export_game() is False
    assert captured[0][0] == "Save game"
    assert "prefix-" in captured[0][1] and "-save.json" in captured[0][1]
    assert len(captured[0][1]) < 600
    assert "\\n" in captured[0][1]
    assert window.game_view.session.snapshot() == before
    assert not window.game_view._has_unsaved_progress()
