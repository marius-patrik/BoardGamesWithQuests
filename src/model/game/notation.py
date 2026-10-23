"""Chess PGN and English-draughts PDN recorded from accepted game actions.

Notation is a presentation/export adapter, not a second rules engine. Every
token is reconstructed through the canonical game manager and verified against
the authoritative final snapshot before any text is emitted.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from model.game.definition import validate_definition
from model.game.manager import GameManager
from model.game.validator import MoveValidator
from model.game.session import DesktopSession

PIECE_LETTERS = {"king": "K", "queen": "Q", "rook": "R", "bishop": "B", "knight": "N", "pawn": ""}


class NotationError(ValueError):
    """The game or output path cannot be safely represented as notation."""


def _escape(value: Any) -> str:
    """Protect PGN/PDN tag syntax from player-chosen identity strings."""
    return (
        str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    )


def _result(state: Mapping[str, Any]) -> str:
    outcome = state["outcome"]
    if outcome is None:
        return "*"
    if outcome["kind"] == "draw":
        return "1/2-1/2"
    if outcome["kind"] == "win":
        white = state["participants"]["1"]
        black = state["participants"]["-1"]
        if outcome["winner"] == white:
            return "1-0"
        if outcome["winner"] == black:
            return "0-1"
    raise NotationError("unrepresentable terminal result")


def _algebraic(square: list[int] | tuple[int, int], rows: int) -> str:
    row, col = square
    if not (0 <= col < 26 and 0 <= row < rows <= 26):
        raise NotationError("standard chess notation requires a bounded board")
    return chr(ord("a") + col) + str(rows - row)


def _pdn_square(square: list[int] | tuple[int, int]) -> str:
    row, col = square
    if not (0 <= row < 8 and 0 <= col < 8 and (row + col) % 2 == 1):
        raise NotationError("PDN requires an English-draughts dark square")
    return str(row * 4 + col // 2 + 1)


def _chess_token(
    before: dict[str, Any],
    after: dict[str, Any],
    action: dict[str, Any],
    event: dict[str, Any],
    offered: list[dict[str, Any]],
    board,
) -> str:
    move = action["move"]
    start, end = move["start"], move["hops"][-1]
    source_piece = next((piece for piece in before["board"] if piece["square"] == start), None)
    if source_piece is None:
        raise NotationError("notation source square contains no moving piece")
    kind = source_piece["kind"]
    if kind not in PIECE_LETTERS:
        raise NotationError("unsupported chess piece kind")
    capture = bool(event["captured"])
    if kind == "king" and abs(end[1] - start[1]) == 2:
        token = "O-O" if end[1] > start[1] else "O-O-O"
    else:
        symbol = PIECE_LETTERS[kind]
        label = _algebraic(end, before["config"]["board"]["rows"])
        disambig = ""
        if kind == "pawn" and capture:
            disambig = chr(ord("a") + start[1])
        elif kind != "pawn":
            alternatives = [
                other["start"]
                for other in offered
                if other["start"] != start
                and other["hops"][-1] == end
                and any(
                    piece["square"] == other["start"] and piece["kind"] == kind
                    for piece in before["board"]
                )
            ]
            if alternatives:
                file_unique = all(sq[1] != start[1] for sq in alternatives)
                rank_unique = all(sq[0] != start[0] for sq in alternatives)
                if file_unique:
                    disambig = chr(ord("a") + start[1])
                elif rank_unique:
                    disambig = str(before["config"]["board"]["rows"] - start[0])
                else:
                    disambig = _algebraic(start, before["config"]["board"]["rows"])
        token = symbol + disambig + ("x" if capture else "") + label
        if move.get("promotion"):
            promotion = move["promotion"]
            if promotion not in PIECE_LETTERS or not PIECE_LETTERS[promotion]:
                raise NotationError("invalid promotion for standard SAN")
            token += "=" + PIECE_LETTERS[promotion]
    defending = after["active_side"]
    if after["outcome"] is None or after["outcome"]["kind"] == "win":
        opposing_king = next(
            (
                piece["square"]
                for piece in after["board"]
                if piece["kind"] == "king" and piece["side"] == defending
            ),
            None,
        )
        if opposing_king is not None:
            checks = MoveValidator(board).is_square_attacked(tuple(opposing_king), -defending)
            if checks:
                terminal = after["outcome"]
                mate = terminal is not None and terminal["kind"] == "win"
                token += "#" if mate else "+"
    return token


def render_notation(state: Mapping[str, Any]) -> tuple[str, str]:
    """Build canonical PGN or PDN only from an exactly replayable game snapshot."""
    current = DesktopSession.recover(state).snapshot()
    variant = current["config"]["name"]
    if variant not in ("chess", "english_draughts"):
        raise NotationError("notation is unavailable for this game")
    extension = ".pgn" if variant == "chess" else ".pdn"
    result = _result(current)
    date = datetime.fromtimestamp(current["started_at_ms"] / 1000, tz=timezone.utc).strftime(
        "%Y.%m.%d"
    )
    tags = [
        ("Event", "BoardGamesWithQuests"),
        ("Site", "Local"),
        ("Date", date),
        ("Round", "-"),
        ("White", current["participants"]["1"]),
        ("Black", current["participants"]["-1"]),
        ("Result", result),
    ]
    if variant == "english_draughts":
        tags.append(("GameType", "21"))
    prefix = "\n".join("[" + key + ' "' + _escape(val) + '"]' for key, val in tags)
    replay = GameManager(
        validate_definition(current["config"], "<notation>"),
        current["game_id"],
        (current["participants"]["1"], current["participants"]["-1"]),
        current["started_at_ms"],
    )
    tokens: list[str] = []
    ply = 0
    for event in current["events"]:
        before = replay.get_state()
        action = event.get("action", {"type": "move", "move": event["move"]})
        offered = (
            [move.to_json() for move in replay.get_valid_moves()]
            if action["type"] == "move"
            else []
        )
        actual = replay.submit_action(
            event["actor"],
            event["expected_revision"],
            event["action_id"],
            action,
            event["at_ms"],
        )
        if actual != event:
            raise NotationError("event does not match authoritative replay")
        if action["type"] != "move":
            continue
        ply += 1
        after = replay.get_state()
        if variant == "chess":
            token = _chess_token(before, after, action, actual, offered, replay.board_projection())
        else:
            move = action["move"]
            sequence = [move["start"], *move["hops"]]
            token = ("x" if actual["captured"] else "-").join(
                _pdn_square(square) for square in sequence
            )
        # Chess opens White; English draughts opens Black.
        if before["active_side"] == 1:
            tokens.append(f"{(ply + 1) // 2}. {token}")
        else:
            if ply == 1:
                tokens.append(f"1... {token}")
            else:
                tokens.append(token)
    if replay.get_state() != current:
        raise NotationError("notation does not reproduce the saved game")
    return extension, prefix + "\n\n" + " ".join([*tokens, result]) + "\n"


def save_notation(session: DesktopSession, path: str | os.PathLike[str]) -> str:
    """Atomically export canonical notation without following file symlinks."""
    extension, content = render_notation(session.snapshot())
    target = Path(path)
    if target.suffix.lower() != extension:
        raise NotationError(f"expected a {extension} filename")
    if target.is_symlink() or not target.parent.is_dir():
        raise NotationError("notation requires a normal file in an existing directory")
    data = content.encode("utf-8")
    if len(data) > 1024 * 1024:
        raise NotationError("notation exceeds the export-size limit")
    temporary = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=".bgwq-notation-",
            suffix=extension,
            dir=target.parent,
        )
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if target.is_symlink():
            raise NotationError("refusing symlinked notation destination")
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
    return extension
