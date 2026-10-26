"""Construct the shipped Tkinter window around one local JSON game session."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from controller.controller import GameController
from controller.window_controller import WindowController, display_game_name
from model.game.games import DEFAULT_GAME, available_games
from model.game.session import DesktopSession
from view.player_game_view import PlayerGameView
from view.settings_dialog import SettingsDialog
from view.start_modal import StartModal

APPLICATION_TITLE = "BoardGamesWithQuests"


def build_application(root: tk.Tk, game: str = DEFAULT_GAME, show_modal: bool = True) -> tk.Tk:
    root.title(f"{APPLICATION_TITLE}")
    # Enforced compact viewport: smaller windows must not silently crop gameplay.
    root.minsize(840, 640)
    style = ttk.Style(root)
    style.theme_use(style.theme_names()[0])
    games = available_games()
    controller = WindowController(GameController(DesktopSession(game)))
    controller.start()
    root.title(controller.game_title())
    shell = ttk.Frame(root)
    shell.pack(fill="both", expand=True)
    view = PlayerGameView(
        shell,
        controller,
        on_settings=lambda: open_settings(root, controller),
        on_new_game_request=lambda: _offer_modal(root, games, controller),
    )
    view.pack(fill="both", expand=True)
    root.game_view = view
    root.window_controller = controller
    root.available_games = games
    view.start_auto_refresh()
    if show_modal:
        root.after(50, lambda: _offer_modal(root, games, controller, initial=True))
    return root


def open_settings(root: tk.Tk, controller: WindowController) -> SettingsDialog:
    dialog = SettingsDialog(
        root,
        on_saved=lambda settings: (
            root.game_view.apply_preferences(settings),
            controller.set_status("Preferences saved."),
        ),
    )
    root.settings_dialog = dialog
    return dialog


def _offer_modal(
    root: tk.Tk, games: list[str], controller: WindowController, *, initial: bool = False
) -> None:
    def start(game: str) -> None:
        controller.game_controller.new_game(game)
        controller.set_status(f"Playing {display_game_name(game)}.")
        root.game_view.reload(clean=True)

    def cancel() -> None:
        # The initial chooser is optional: an already running default session
        # remains playable. Later New game cancellation is a strict no-op.
        if initial:
            controller.set_status("Continuing the default game.")
            root.game_view.refresh()

    StartModal(
        root,
        games=games,
        default=controller.game_controller.session.game,
        on_start=start,
        on_settings=lambda: open_settings(root, controller),
        on_cancel=cancel,
    )
