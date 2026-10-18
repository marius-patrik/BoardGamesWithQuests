"""Test session setup.

The shared Tkinter root is provided only when a display is available.
"""

import tkinter as tk

import pytest



@pytest.fixture(scope="session")
def tk_root():
    """Yield one Tk root for the whole session.

    Destroying the last Tk root in a process tears down the Tcl interpreter, and building a new
    root afterwards segfaults rather than raising. So every test that needs a window uses this
    one root, and none of them destroys it. Where there is no display the fixture skips, so a
    headless run of the suite still works.

    Yields:
        tk.Tk: A withdrawn root, ready to build widgets into.
    """
    try:
        root = tk.Tk()
    except tk.TclError as error:  # pragma: no cover - depends on the machine
        pytest.skip(f"no display available: {error}")
    root.withdraw()
    yield root
