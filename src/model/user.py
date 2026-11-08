"""Local player identity, durable profile storage and error recovery."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


def data_directory() -> Path:
    if os.getenv("BOARDGAMESWITHQUESTS_DATA_DIR"):
        return Path(os.environ["BOARDGAMESWITHQUESTS_DATA_DIR"]).expanduser()
    if sys.platform == "win32":
        return (
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
            / "BoardGamesWithQuests"
        )
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "BoardGamesWithQuests"
    return (
        Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
        / "boardgameswithquests"
    )


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".save-",
            suffix=".tmp",
            delete=False,
        ) as f:
            tmp = f.name
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def normalize_username(username: str) -> str:
    if not isinstance(username, str):
        raise ValueError("Username must be text")
    value = username.strip().casefold()
    if not value or len(value) > 60 or any(ord(c) < 32 for c in value):
        raise ValueError("Username must contain 1–60 printable characters")
    return value


@dataclass
class Uzivatel:
    uzivatelske_jmeno: str
    jmeno: str
    xp: int = 0


class UserManager:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else data_directory()
        self.path = self.root / "users.json"
        self.uzivatele: dict[str, Uzivatel] = {}
        self.save_error: str | None = None
        self.damaged = False
        self.dirty = False
        self.nacti_uzivatele()

    @staticmethod
    def _read_profiles(path: Path) -> dict[str, Uzivatel]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(raw, dict)
            or raw.get("schema_version") != 1
            or not isinstance(raw.get("users"), dict)
        ):
            raise ValueError("Unsupported profile format")
        loaded: dict[str, Uzivatel] = {}
        for key, user in raw["users"].items():
            if not isinstance(user, dict) or type(user.get("xp")) is not int or user["xp"] < 0:
                raise ValueError("Invalid XP")
            username = normalize_username(user["username"])
            if (
                username != key
                or not isinstance(user.get("display_name"), str)
                or not user["display_name"].strip()
            ):
                raise ValueError("Invalid profile")
            loaded[key] = Uzivatel(key, user["display_name"], user["xp"])
        return loaded

    def nacti_uzivatele(self) -> None:
        if not self.path.exists():
            return
        try:
            self.uzivatele = self._read_profiles(self.path)
            self.damaged = False
            self.save_error = None
        except (ValueError, OSError, TypeError, KeyError, UnicodeError) as exc:
            self.uzivatele = {}
            self.damaged = True
            self.save_error = f"Profile file needs repair: {exc}. Original was preserved."

    def _recover_for_retry(self) -> bool:
        """Explicit retry after external repair/removal; never overwrite conflicting profiles."""
        if not self.damaged:
            return True
        recovered: dict[str, Uzivatel] = {}
        if self.path.exists():
            try:
                recovered = self._read_profiles(self.path)
            except (ValueError, OSError, TypeError, KeyError, UnicodeError) as exc:
                self.save_error = f"Profile file is still damaged: {exc}. Original was preserved."
                return False
        conflicting = [
            name
            for name, saved in recovered.items()
            if name in self.uzivatele and self.uzivatele[name] != saved
        ]
        if conflicting:
            self.save_error = (
                "Repaired profile file conflicts with in-memory profiles ("
                + ", ".join(sorted(conflicting))
                + "). Resolve the differences or move the repaired file aside before retrying."
            )
            return False
        # Retain live objects referenced by the current GameManager's player seats.
        self.uzivatele = {**recovered, **self.uzivatele}
        self.damaged = False
        self.dirty = True
        return True

    def vytvor_uzivatele(self, username: str, display_name: str) -> Uzivatel:
        key = normalize_username(username)
        name = display_name.strip()
        if not name or len(name) > 80:
            raise ValueError("Display name must contain 1–80 characters")
        if key in self.uzivatele:
            raise ValueError("This username already exists")
        user = Uzivatel(key, name)
        self.uzivatele[key] = user
        self.dirty = True
        self.uloz_uzivatele()
        return user

    def pridej_xp(self, username: str, amount: int) -> None:
        if type(amount) is not int or amount < 0:
            raise ValueError("Invalid XP amount")
        self.uzivatele[normalize_username(username)].xp += amount
        self.dirty = True

    def uloz_uzivatele(self) -> bool:
        if not self._recover_for_retry():
            return False
        try:
            atomic_json(
                self.path,
                {
                    "schema_version": 1,
                    "users": {
                        k: {
                            "username": u.uzivatelske_jmeno,
                            "display_name": u.jmeno,
                            "xp": u.xp,
                        }
                        for k, u in sorted(self.uzivatele.items())
                    },
                },
            )
            self.dirty = False
            self.save_error = None
            return True
        except OSError as exc:
            self.dirty = True
            self.save_error = f"Profiles were not saved: {exc}"
            return False
