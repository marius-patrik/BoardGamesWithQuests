"""Player-facing settings: validated display preferences, never game rule editing."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from model.preferences import (
    DEFAULTS,
    PreferencesError,
    load_preferences,
    save_preferences,
)
from view.dialog_lifecycle import ModalLifecycle


class SettingsDialog:
    """Edit only supported persistent presentation preferences."""

    def __init__(
        self,
        master: tk.Misc,
        on_saved: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.on_saved = on_saved
        self.window = tk.Toplevel(master)
        self.window.title("Settings")
        self._modal = ModalLifecycle(self.window, master)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())
        self.window.bind("<Return>", lambda _event: self.save())

        try:
            values = load_preferences()
            warning = ""
        except PreferencesError as error:
            values = dict(DEFAULTS)
            warning = f"Saved settings could not be read: {error}"
        self.size = tk.IntVar(master=self.window, value=values["board_size"])
        self.coordinates = tk.BooleanVar(master=self.window, value=values["show_coordinates"])

        body = ttk.Frame(self.window, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Preferred square size (32–88 px)").pack(anchor="w")
        self.size_control = ttk.Spinbox(body, from_=32, to=88, textvariable=self.size, width=7)
        self.size_control.pack(anchor="w", pady=(4, 6))
        ttk.Label(
            body,
            text="The board automatically fits smaller windows. "
            "Your preferred size is its maximum.",
            wraplength=325,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))
        ttk.Checkbutton(body, text="Show board coordinates", variable=self.coordinates).pack(
            anchor="w"
        )
        if warning:
            ttk.Label(body, text=warning, wraplength=325, justify="left").pack(
                anchor="w", pady=(10, 0)
            )
        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(18, 0))
        ttk.Button(buttons, text="Restore defaults", command=self.restore_defaults).pack(
            side="left"
        )
        ttk.Button(buttons, text="Cancel", command=self.close).pack(side="right")
        self.save_button = ttk.Button(buttons, text="Save", command=self.save)
        self.save_button.pack(side="right", padx=(0, 8))
        self._modal.center()
        self._modal.activate(self.size_control)

    def restore_defaults(self) -> None:
        """Reset the fields locally; persist only after Save is selected."""
        self.size.set(DEFAULTS["board_size"])
        self.coordinates.set(DEFAULTS["show_coordinates"])

    def save(self) -> None:
        try:
            values = save_preferences(
                {
                    "board_size": self.size.get(),
                    "show_coordinates": self.coordinates.get(),
                }
            )
        except (ValueError, tk.TclError, OSError) as error:
            messagebox.showerror(
                "Settings",
                f"Preferences were not saved:\n{error}",
                parent=self.window,
            )
            return
        if self.on_saved is not None:
            self.on_saved(values)
        self.close()

    def close(self) -> None:
        self._modal.close()
