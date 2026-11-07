"""Native Tk modal grab and focus restoration for sequential/nested dialogs.

The lifecycle object owns presentation only, never game state or acceptance.
"""

from __future__ import annotations

import tkinter as tk


class ModalLifecycle:
    """Return a transient modal's focus and grab to its previous owner."""

    def __init__(self, window: tk.Toplevel, parent: tk.Misc) -> None:
        self.window = window
        self.parent = parent.winfo_toplevel()
        self._previous_grab = window.grab_current()
        self._previous_focus = window.focus_get()
        self._closed = False
        window.transient(self.parent)

    def activate(self, focus: tk.Misc) -> None:
        """Present an already laid-out window with a single local modal grab."""
        self.window.update_idletasks()
        self.window.grab_set()
        focus.focus_set()

    def center(self) -> None:
        """Center over the owning window without changing a game's geometry."""
        self.window.update_idletasks()
        try:
            x = (
                self.parent.winfo_rootx()
                + (self.parent.winfo_width() - self.window.winfo_reqwidth()) // 2
            )
            y = (
                self.parent.winfo_rooty()
                + (self.parent.winfo_height() - self.window.winfo_reqheight()) // 2
            )
            self.window.geometry(f"+{max(0, x)}+{max(0, y)}")
        except tk.TclError:
            pass

    def close(self) -> None:
        """Release this modal and reinstate a still-existing parent modal."""
        if self._closed:
            return
        self._closed = True
        try:
            if self.window.grab_current() == self.window:
                self.window.grab_release()
        except tk.TclError:
            pass
        self.window.destroy()

        try:
            owner = self._previous_grab
            if owner is not None and owner.winfo_exists() and owner.winfo_ismapped():
                owner.grab_set()
            focus = self._previous_focus
            if focus is None or not focus.winfo_exists():
                focus = self.parent
            if focus.winfo_exists():
                focus.focus_set()
        except tk.TclError:
            # Closing the application can destroy the parent during unwinding.
            pass
