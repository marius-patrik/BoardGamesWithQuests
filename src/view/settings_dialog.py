"""Player-facing settings: validated display preferences, never game rule editing."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from model.game.preferences import (
    DEFAULTS,
    PreferencesError,
    load_preferences,
    save_preferences,
)


class SettingsDialog:
    """Edit only the supported persistent presentation preferences."""

    def __init__(
        self,
        master: tk.Misc,
        on_saved: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.on_saved = on_saved
        self.window = tk.Toplevel(master)
        self.window.title("Settings")
        self.window.transient(master)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        try:
            values = load_preferences()
            warning = ""
        except PreferencesError as error:
            values = dict(DEFAULTS)
            warning = f"Saved preferences were invalid: {error}"
        self.size = tk.IntVar(value=values["board_size"])
        self.coordinates = tk.BooleanVar(value=values["show_coordinates"])
        body = ttk.Frame(self.window, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Board size (32–88)").pack(anchor="w")
        ttk.Spinbox(body, from_=32, to=88, textvariable=self.size, width=7).pack(
            anchor="w", pady=(2, 8)
        )
        ttk.Checkbutton(body, text="Show board coordinates",
                        variable=self.coordinates).pack(anchor="w")
        if warning:
            ttk.Label(body, text=warning, wraplength=300).pack(anchor="w", pady=8)
        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="Save", command=self.save).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=self.close).pack(
            side="left", padx=(8, 0)
        )

    def save(self) -> None:
        try:
            values = save_preferences({
                "board_size": self.size.get(),
                "show_coordinates": self.coordinates.get(),
            })
        except (ValueError, tk.TclError, OSError) as error:
            messagebox.showerror("Settings", str(error), parent=self.window)
            return
        if self.on_saved is not None:
            self.on_saved(values)
        self.close()

    def close(self) -> None:
        try:
            self.window.grab_release()
        except tk.TclError:
            pass
        self.window.destroy()
