"""The original Canvas board renderer and pointer-to-square projection.

Board markers describe the current session's legal destinations and committed
moves; no game rules or mutable game state live in this view.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from model.game.board import Board
from model.pieces.piece import Piece

Square = tuple[int, int]

LIGHT = "#f0d9b5"
DARK = "#b58863"
SELECTED = "#1255a3"
QUIET_TARGET = "#205c38"
CAPTURE_TARGET = "#8b2351"
IN_CHECK = "#bf303e"


class BoardView(ttk.Frame):
    """Draw pieces, coordinates and distinct pointer-visible interaction states."""

    def __init__(
        self,
        master: tk.Misc,
        board: Board,
        on_square_clicked: Callable[[Square], None] | None = None,
        square_size: int = 56,
        show_coordinates: bool = True,
    ):
        super().__init__(master)
        self.board = board
        self.on_square_clicked = on_square_clicked
        self.square_size = square_size
        self.show_coordinates = show_coordinates
        self.selected: Square | None = None
        self.targets: list[Square] = []
        self.in_check: Square | None = None
        self.last_move: tuple[Square, Square] | None = None
        self.hovered: Square | None = None
        self.invalid: Square | None = None
        self._invalid_after: str | None = None
        self._appearance = {"light_square": LIGHT, "dark_square": DARK}
        self._draughts = False

        self.canvas = tk.Canvas(
            self,
            width=board.cols * square_size,
            height=board.rows * square_size,
            highlightthickness=0,
            background=LIGHT,
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._clicked)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.redraw()

    def set_appearance(self, appearance: dict[str, str], *, draughts: bool = False) -> None:
        """Use the validated game's own square palette and piece family."""
        palette = {
            "light_square": appearance.get("light_square", LIGHT),
            "dark_square": appearance.get("dark_square", DARK),
        }
        if palette != self._appearance or draughts != self._draughts:
            self._appearance = palette
            self._draughts = draughts
            self.redraw()

    def refresh(self, board: Board | None = None) -> None:
        """Refresh the detached board projection, keeping click geometry aligned."""
        if board is not None:
            self.board = board
        self._fit_canvas()
        self.redraw()

    def _fit_canvas(self) -> None:
        self.canvas.configure(
            width=self.board.cols * self.square_size,
            height=self.board.rows * self.square_size,
        )

    def fit_to(self, width: int, height: int, preferred_size: int) -> None:
        """Keep the entire board visible while honoring saved maximum square size."""
        size = max(
            1,
            min(
                preferred_size,
                max(1, width // self.board.cols),
                max(1, height // self.board.rows),
            ),
        )
        if size != self.square_size:
            self.square_size = size
            self._fit_canvas()
            self.redraw()

    def set_selection(self, selected: Square | None, targets: list[Square]) -> None:
        if selected != self.selected or targets != self.targets:
            self.selected = selected
            self.targets = list(targets)
            self.redraw()

    def set_in_check(self, square: Square | None) -> None:
        if square != self.in_check:
            self.in_check = square
            self.redraw()

    def set_last_move(self, start: Square | None, end: Square | None) -> None:
        move = (start, end) if start is not None and end is not None else None
        if move != self.last_move:
            self.last_move = move
            self.redraw()

    def show_invalid_square(self, square: Square) -> None:
        """Temporarily mark a rejected destination with a non-color X."""
        if self._invalid_after is not None:
            self.after_cancel(self._invalid_after)
        self.invalid = square
        self.redraw()
        self._invalid_after = self.after(650, self._clear_invalid)

    def _clear_invalid(self) -> None:
        self._invalid_after = None
        self.invalid = None
        self.redraw()

    def redraw(self) -> None:
        """Repaint one Canvas, including legible compact-square markers."""
        self.canvas.delete("all")
        board = self.board
        size = self.square_size
        targets = set(self.targets)

        for row in range(board.rows):
            for col in range(board.cols):
                square = (row, col)
                left, top = self._origin(col, row)
                right, bottom = left + size, top + size
                light = (row + col) % 2 == 0
                fill = self._appearance["light_square" if light else "dark_square"]
                self.canvas.create_rectangle(
                    left, top, right, bottom, fill=fill, outline="#66584b", tags=("square",)
                )

                if self.last_move is not None and square in self.last_move:
                    self.canvas.create_rectangle(
                        left + 3,
                        top + 3,
                        right - 3,
                        bottom - 3,
                        outline="#174f67",
                        width=2,
                        dash=(4, 3),
                        tags=("last_move",),
                    )

                if square == self.in_check:
                    self.canvas.create_rectangle(
                        left + 1,
                        top + 1,
                        right - 1,
                        bottom - 1,
                        outline=IN_CHECK,
                        width=3,
                        tags=("in_check",),
                    )
                    self.canvas.create_text(
                        right - 6, top + 4, anchor="ne", text="!",
                        fill=IN_CHECK, font=("TkDefaultFont", max(9, size // 4), "bold"),
                        tags=("in_check",),
                    )

                piece = board.get_piece_at(square)
                if piece is not None:
                    self._draw_piece(piece, left, top, right, bottom)
                if square in targets:
                    # An occupied opponent is a capture target; other moves
                    # are shown as empty landing squares. The engine alone
                    # decides which squares belong in targets.
                    occupied_capture = (
                        piece is not None
                        and self.selected is not None
                        and (origin := board.get_piece_at(self.selected)) is not None
                        and piece.getColor() != origin.getColor()
                    )
                    if occupied_capture:
                        self._draw_capture_target(left, top, right, bottom)
                    else:
                        self._draw_quiet_target(left, top, right, bottom)

                if square == self.selected:
                    self.canvas.create_rectangle(
                        left + 2, top + 2, right - 2, bottom - 2,
                        outline="#ffffff", width=5, tags=("selected",)
                    )
                    self.canvas.create_rectangle(
                        left + 3, top + 3, right - 3, bottom - 3,
                        outline=SELECTED, width=3, tags=("selected",)
                    )

                if square == self.hovered:
                    self.canvas.create_rectangle(
                        left + 1, top + 1, right - 1, bottom - 1,
                        outline="#ffffff", width=2, dash=(3, 3), tags=("hover",)
                    )

                if square == self.invalid:
                    offset = max(9, size // 4)
                    cx, cy = (left + right) / 2, (top + bottom) / 2
                    for colour, width in (("#ffffff", 5), ("#b42330", 3)):
                        self.canvas.create_line(
                            cx - offset, cy - offset, cx + offset, cy + offset,
                            fill=colour, width=width, tags=("invalid",)
                        )
                        self.canvas.create_line(
                            cx - offset, cy + offset, cx + offset, cy - offset,
                            fill=colour, width=width, tags=("invalid",)
                        )

        if self.show_coordinates:
            self._draw_coordinates()

    def _origin(self, col: int, row: int) -> Square:
        return col * self.square_size, row * self.square_size

    def _draw_piece(self, piece: Piece, left: int, top: int, right: int, bottom: int) -> None:
        size = self.square_size
        centre = ((left + right) / 2, (top + bottom) / 2)
        if self._draughts:
            white = piece.getColor() == 1
            margin = max(4, round(size * 0.15))
            outer = (left + margin, top + margin, right - margin, bottom - margin)
            # A double-rimmed filled coin remains identifiable even without
            # fonts supporting the bundled draughts Unicode symbols.
            self.canvas.create_oval(
                *outer,
                fill="#f9f6e8" if white else "#26333e",
                outline="#24272a" if white else "#f5e5bc",
                width=max(2, size // 16),
                tags=("piece", "draughts_piece"),
            )
            self.canvas.create_oval(
                left + margin + 4, top + margin + 4,
                right - margin - 4, bottom - margin - 4,
                outline="#777063" if white else "#c0ad87",
                width=2,
                tags=("piece", "draughts_piece"),
            )
            if piece.getType() == "king":
                # Explicit crown glyph plus a ring distinguish kings from men
                # in monochrome and at the compact 32 px square size.
                self.canvas.create_text(
                    *centre, text="K", fill="#24272a" if white else "#ffffff",
                    font=("TkDefaultFont", max(10, round(size * 0.36)), "bold"),
                    tags=("piece", "draughts_king"),
                )
            else:
                self.canvas.create_oval(
                    centre[0] - 2, centre[1] - 2, centre[0] + 2, centre[1] + 2,
                    fill="#696157" if white else "#ded4b9", outline="",
                    tags=("piece", "draughts_man"),
                )
            return

        glyph = piece.getSymbol() or piece.getName()
        font = ("TkDefaultFont", max(14, round(size * 0.67)))
        white = piece.getColor() == 1
        self.canvas.create_text(
            centre[0] + 1, centre[1] + 1,
            text=glyph, fill="#18232c" if white else "#f8efe2",
            font=font, tags=("piece",),
        )
        self.canvas.create_text(
            *centre, text=glyph, fill="#fffaf0" if white else "#17191e",
            font=font, tags=("piece",),
        )

    def _draw_quiet_target(self, left: int, top: int, right: int, bottom: int) -> None:
        size = self.square_size
        radius = max(4, size * 0.12)
        cx, cy = (left + right) / 2, (top + bottom) / 2
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill=QUIET_TARGET, outline="#ffffff", width=2, tags=("legal_quiet",)
        )

    def _draw_capture_target(self, left: int, top: int, right: int, bottom: int) -> None:
        margin = max(3, self.square_size // 12)
        for colour, width, dash in (("#ffffff", 5, ()), (CAPTURE_TARGET, 3, (5, 3))):
            self.canvas.create_oval(
                left + margin, top + margin, right - margin, bottom - margin,
                outline=colour, width=width, dash=dash, tags=("legal_capture",)
            )

    def _draw_coordinates(self) -> None:
        """Put ranks/files in square corners, outside the central piece glyphs."""
        size = self.square_size
        font = ("TkDefaultFont", max(7, min(10, size // 5)), "bold")
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                light = (row + col) % 2 == 0
                ink = "#30251f" if light else "#fff3da"
                x, y = self._origin(col, row)
                if col == 0:
                    self.canvas.create_text(
                        x + 3, y + 2, anchor="nw",
                        text=str(self.board.rows - row), fill=ink,
                        font=font, tags=("coordinate",),
                    )
                if row == self.board.rows - 1:
                    self.canvas.create_text(
                        x + size - 3, y + size - 2, anchor="se",
                        text=self._file_label(col), fill=ink,
                        font=font, tags=("coordinate",),
                    )

    @staticmethod
    def _file_label(col: int) -> str:
        return chr(ord("a") + col)

    def _square_at(self, x: int, y: int) -> Square | None:
        if x < 0 or y < 0:
            return None
        row, col = y // self.square_size, x // self.square_size
        return (row, col) if self.board.is_within_bounds(row, col) else None

    def _on_motion(self, event: tk.Event) -> None:
        square = self._square_at(event.x, event.y)
        if square != self.hovered:
            self.hovered = square
            self.redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        if self.hovered is not None:
            self.hovered = None
            self.redraw()

    def _clicked(self, event: tk.Event) -> None:
        if self.on_square_clicked is not None:
            square = self._square_at(event.x, event.y)
            if square is not None:
                self.on_square_clicked(square)

    def destroy(self) -> None:
        if self._invalid_after is not None:
            self.after_cancel(self._invalid_after)
        super().destroy()
