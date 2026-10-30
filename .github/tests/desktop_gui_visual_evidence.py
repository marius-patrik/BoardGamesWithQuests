"""Capture genuine Tk/Xvfb windows for the #452 board layout evidence gate.

Run: xvfb-run -a -s '-screen 0 1920x1200x24' python .github/tests/desktop_gui_visual_evidence.py
This utility captures the actual display, not a synthetic Canvas export.
"""

from __future__ import annotations

import base64
from io import BytesIO
import os
from pathlib import Path
import tkinter as tk

from PIL import ImageGrab

from view.app import build_application


def click(root: tk.Tk, row: int, col: int) -> None:
    canvas = root.game_view.board_view.canvas
    size = root.game_view.board_view.square_size
    canvas.event_generate("<Button-1>", x=(col * size + size // 2), y=(row * size + size // 2))
    root.update()


def capture(root: tk.Tk, filename: Path) -> None:
    root.update_idletasks()
    root.update()
    x, y = root.winfo_rootx(), root.winfo_rooty()
    width, height = root.winfo_width(), root.winfo_height()
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height), xdisplay=os.environ["DISPLAY"])
    assert image.size == (width, height)
    assert len(image.resize((64, 64)).getcolors(4096) or []) > 5
    image.save(filename)
    thumbnail = image.copy()
    thumbnail.thumbnail((510, 340))
    packed = BytesIO()
    thumbnail.save(packed, format="WEBP", quality=55)
    print(f"UX452_IMAGE:{filename.name}:{base64.b64encode(packed.getvalue()).decode()}", flush=True)


def main() -> None:
    output = Path("ux452-real-screenshots")
    output.mkdir(exist_ok=True)
    for game in ("chess", "checkers"):
        for width, height in ((840, 640), (1100, 760), (1440, 900)):
            root = tk.Tk()
            root.geometry(f"{width}x{height}+0+0")
            build_application(root, game, show_modal=False)
            try:
                root.update()
                view = root.game_view
                board = view.board_view
                assert view.player_views[1].winfo_rootx() < board.winfo_rootx()
                assert board.winfo_rootx() < view.player_views[-1].winfo_rootx()
                assert view.quest_viewports[1].winfo_ismapped()
                assert view.quest_viewports[-1].winfo_ismapped()
                capture(root, output / f"ux452-after-{game}-{width}x{height}.png")
                if game == "chess":
                    click(root, 6, 4)
                    assert board.canvas.find_withtag("legal_quiet")
                    click(root, 4, 4)
                else:
                    click(root, 2, 3)
                    assert board.canvas.find_withtag("legal_quiet")
                    click(root, 3, 2)
                assert view.session.snapshot()["revision"] == 1
                capture(root, output / f"ux452-after-{game}-{width}x{height}-moved.png")
            finally:
                root.game_view.stop_auto_refresh()
                root.destroy()


if __name__ == "__main__":
    main()
