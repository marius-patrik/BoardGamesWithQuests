"""Versioned, one-file-per-match chronological accepted-action record."""

from __future__ import annotations
import json
import uuid
from pathlib import Path
from model.move import Tah
from model.user import atomic_json, data_directory


class GameLogger:
    def __init__(self, white: str, black: str, root: Path | None = None) -> None:
        self.match_id = str(uuid.uuid4())
        self.root = Path(root) if root is not None else data_directory()
        self.path = self.root / "logs" / f"{self.match_id}.json"
        self.players = {"white": white, "black": black}
        self.events: list[dict] = []
        self.status = "in_progress"
        self.result: dict[str, str | None] = {"reason": None, "winner": None}
        self.save_error: str | None = None
        self.dirty = True
        self.damaged = False

    @property
    def predchozi_tah(self) -> Tah | None:
        for event in reversed(self.events):
            if event["type"] == "move":
                return Tah(
                    tuple(event["from"]),
                    tuple(event["to"]),
                    event["move_kind"],
                    event["promotion"],
                )
        return None

    def zaznamenej(self, data: dict, reason: str | None, winner: str | None) -> None:
        self.events.append({"index": len(self.events) + 1, **data})
        if reason:
            self.status = "terminal"
            self.result = {
                "reason": reason,
                "winner": self.players.get(winner) if winner else None,
            }
        self.dirty = True

    def zapis(self) -> dict:
        return {
            "schema_version": 1,
            "match_id": self.match_id,
            "players": self.players,
            "events": self.events,
            "status": self.status,
            "result": self.result,
        }

    def uloz_historii(self) -> bool:
        if self.damaged:
            self.save_error = (
                "Damaged match file must be repaired or moved before saving"
            )
            return False
        try:
            if self.path.exists():
                try:
                    existing = json.loads(self.path.read_text(encoding="utf-8"))
                    if (
                        not isinstance(existing, dict)
                        or existing.get("schema_version") != 1
                        or existing.get("match_id") != self.match_id
                        or not isinstance(existing.get("events"), list)
                    ):
                        raise ValueError("Invalid match file")
                except (ValueError, UnicodeError) as exc:
                    self.damaged = True
                    raise ValueError(
                        "Existing match file is damaged and was preserved"
                    ) from exc
            atomic_json(self.path, self.zapis())
            self.save_error = None
            self.dirty = False
            return True
        except (OSError, ValueError) as exc:
            self.dirty = True
            self.save_error = f"History was not saved: {exc}"
            return False
