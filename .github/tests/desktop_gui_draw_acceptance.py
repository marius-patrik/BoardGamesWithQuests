"""Real pointer/Tk draw actions and complete canonical claim route acceptance.

Run with Xvfb; dialog widgets are real. The callback only actuates visible
buttons/selection as a human would, without replacing the gameplay engine.
"""

from __future__ import annotations

from importlib import resources
import json
import tkinter as tk
from tkinter import ttk

import pytest

from model.definition import validate_definition
from model.session import DesktopSession
from view.app import build_application


@pytest.fixture
def window(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    root = tk.Tk()
    root.geometry("1100x860")
    build_application(root, "chess", show_modal=False)
    root.update()
    try:
        yield root
    finally:
        root.game_view.stop_auto_refresh()
        root.destroy()


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def click_dialog_button(root, label):
    top = next(child for child in descendants(root) if isinstance(child, tk.Toplevel))
    for child in descendants(top):
        if isinstance(child, tk.Listbox):
            child.selection_clear(0, tk.END)
            child.selection_set(0)
            child.activate(0)
        if isinstance(child, ttk.Button) and child.cget("text") == label:
            child.invoke()
            return
    raise AssertionError(f"actual modal lacks clickable {label!r} button")


def square(name):
    return [8 - int(name[1]), ord(name[0]) - ord("a")]


def chess_advance(session, uci):
    state = session.snapshot()
    options = [
        move
        for move in session.legal_actions()
        if move["start"] == square(uci[:2]) and move["hops"][-1] == square(uci[2:4])
    ]
    assert len(options) == 1
    session.submit(
        state["participants"][str(state["active_side"])],
        state["revision"],
        {"type": "move", "move": options[0]},
    )


def draw_ready_chess():
    session = DesktopSession("chess")
    for uci in ("g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"):
        chess_advance(session, uci)
    return session


def draw_ready_wcdf(monkeypatch):
    import model.session as session_module

    data = json.loads(resources.files("games").joinpath("checkers", "config.json").read_text())
    data["board"]["starting_pieces"] = [
        {"piece": "king", "color": "black", "squares": [[2, 1]]},
        {"piece": "king", "color": "white", "squares": [[5, 6]]},
    ]
    definition = validate_definition(data)
    with monkeypatch.context() as patch:
        patch.setattr(session_module, "load_bundled_definition", lambda _: definition)
        session = DesktopSession("checkers")
    route = (
        {"start": [2, 1], "hops": [[3, 2]], "promotion": None},
        {"start": [5, 6], "hops": [[4, 5]], "promotion": None},
        {"start": [3, 2], "hops": [[2, 1]], "promotion": None},
        {"start": [4, 5], "hops": [[5, 6]], "promotion": None},
    )
    for index in range(7):
        state = session.snapshot()
        session.submit(
            state["participants"][str(state["active_side"])],
            state["revision"],
            {"type": "move", "move": route[index % 4]},
        )
    return session


def test_real_offer_accept_and_terminal_controls(window, monkeypatch):
    from view import player_game_view as view

    monkeypatch.setattr(view.simpledialog, "askinteger", lambda *a, **k: 1)
    monkeypatch.setattr(view.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(view.messagebox, "askyesnocancel", lambda *a, **k: True)
    chess_advance(window.game_view.session, "g1f3")
    chess_advance(window.game_view.session, "g8f6")
    window.game_view.refresh()
    before = window.game_view.session.snapshot()
    window.game_view.offer_draw()
    pending = window.game_view.session.snapshot()
    assert pending["pending_draw_offer"]["actor"] == "white"
    assert pending["board"] == before["board"] and pending["outcome"] is None
    assert not window.game_view.action_buttons["Respond draw"].instate(["disabled"])
    window.game_view.respond_draw()
    final = window.game_view.session.snapshot()
    assert final["outcome"]["cause"] == "agreement"
    assert "Draw" in window.game_view.turn.get()
    for name in ("Claim draw", "Offer draw", "Respond draw", "Resign"):
        assert window.game_view.action_buttons[name].instate(["disabled"])
    assert DesktopSession.recover(final).snapshot() == final


def test_wcdf_real_offer_reject_preserves_game_and_clock_anchor(window, monkeypatch):
    from view import player_game_view as view

    window.window_controller.game_controller.new_game("checkers")
    window.game_view.reload(clean=True)
    assert window.game_view.action_buttons["Offer draw"].instate(["disabled"])
    session = window.game_view.session
    state = session.snapshot()
    legal = session.legal_actions()[0]
    session.submit(
        state["participants"][str(state["active_side"])],
        state["revision"],
        {"type": "move", "move": legal},
    )
    window.game_view.refresh()
    before = session.snapshot()
    assert not window.game_view.action_buttons["Offer draw"].instate(["disabled"])
    monkeypatch.setattr(view.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(view.messagebox, "askyesnocancel", lambda *a, **k: False)
    window.game_view.offer_draw()
    assert session.snapshot()["pending_draw_offer"]["actor"] == "black"
    window.game_view.respond_draw()
    after = session.snapshot()
    assert after["outcome"] is None
    assert after["pending_draw_offer"] is None
    assert after["board"] == before["board"]
    assert after["clocks"] == before["clocks"]
    assert DesktopSession.recover(after).snapshot() == after


@pytest.mark.parametrize("game", ["chess", "checkers"])
@pytest.mark.parametrize("button", ["Cancel", "Use intended move"])
def test_real_prospective_claim_modal_cancellation_or_acceptance(window, monkeypatch, game, button):
    from view import player_game_view as view

    session = draw_ready_chess() if game == "chess" else draw_ready_wcdf(monkeypatch)
    window.window_controller.game_controller.session = session
    window.game_view.reload(clean=True)
    state = session.snapshot()
    assert session.draw_claim_candidates("threefold")["intended_moves"]
    assert state["outcome"] is None
    monkeypatch.setattr(view.simpledialog, "askinteger", lambda *a, **k: 1)
    errors = []
    monkeypatch.setattr(view.messagebox, "showerror", lambda *a, **k: errors.append(a))
    window.after(50, lambda: click_dialog_button(window, button))
    window.game_view.claim_draw()
    assert not errors
    after = session.snapshot()
    if button == "Cancel":
        assert after == state
    else:
        assert after["board"] == state["board"]
        assert after["outcome"]["kind"] == "draw"
        assert after["outcome"]["cause"] == "threefold"
        assert after["events"][-1]["move"] is None
        assert DesktopSession.recover(after).snapshot() == after


def test_actual_legal_multi_hop_route_is_displayed_complete_and_cancelable(window, monkeypatch):
    import model.session as session_module

    data = json.loads(resources.files("games").joinpath("checkers", "config.json").read_text())
    data["board"]["starting_pieces"] = [
        {"piece": "man", "color": "black", "squares": [[2, 3]]},
        {"piece": "man", "color": "white", "squares": [[3, 2], [3, 4], [5, 4]]},
        {"piece": "man", "color": "white", "squares": [[7, 0]]},
    ]
    with monkeypatch.context() as patch:
        patch.setattr(
            session_module, "load_bundled_definition", lambda _: validate_definition(data)
        )
        session = DesktopSession("checkers")
    window.window_controller.game_controller.session = session
    window.game_view.reload(clean=True)
    choices = session.legal_actions()
    assert any(len(move["hops"]) > 1 for move in choices)
    before = session.snapshot()
    shown = []

    def inspect_and_cancel():
        modal = next(child for child in descendants(window) if isinstance(child, tk.Toplevel))
        listing = next(child for child in descendants(modal) if isinstance(child, tk.Listbox))
        shown.extend(listing.get(0, tk.END))
        click_dialog_button(window, "Cancel")

    window.after(50, inspect_and_cancel)
    assert window.game_view._choose_intended_move(choices, 8) is None
    assert any(" → " in route and route.count(" → ") >= 2 for route in shown)
    assert session.snapshot() == before
