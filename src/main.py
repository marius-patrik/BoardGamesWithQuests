"""BoardGamesWithQuests desktop and frozen-application verification entry point."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from view.app import BoardGamesApplication, run


def native_self_test() -> int:
    """Exercise real Tk widgets in the frozen process and verify local persistence.

    Intended for distribution acceptance on Windows; never writes user profiles.
    The optional BGW_SMOKE_REPORT file lets GUI-subsystem executables return
    diagnostics when stdout is unavailable.
    """
    result: dict[str, object] = {"status": "fail", "checks": []}
    app: BoardGamesApplication | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="bgw-native-") as tmp:
            root = Path(tmp)
            app = BoardGamesApplication(root)
            app.users.vytvor_uzivatele("alice", "Alice")
            app.users.vytvor_uzivatele("bob", "Bob")
            app.show_setup()
            app.seat_choices["white"].set("alice")
            app.seat_choices["black"].set("bob")
            app.start_match()
            app.update()
            assert len(app.board.buttons) == 64
            result["checks"].append("64 rendered Tkinter buttons")
            for square in ((6, 4), (4, 4), (1, 3), (3, 3), (4, 4), (3, 3)):
                app.board.buttons[square].invoke()
                app.update()
            assert app.manager is not None and app.manager.revision == 3
            assert app.users.uzivatele["alice"].xp == 10
            assert app.manager.logger.path.exists()
            saved_history = json.loads(
                app.manager.logger.path.read_text(encoding="utf-8")
            )
            saved_profiles = json.loads(app.users.path.read_text(encoding="utf-8"))
            assert len(saved_history["events"]) == 3
            assert saved_profiles["users"]["alice"]["xp"] == 10
            result["checks"].extend(
                (
                    "accepted native Tkinter pointer-action lifecycle",
                    "quest XP and JSON saved outside checkout",
                )
            )
            app.controller.odstup()
            app.update()
            assert app.manager.stav == "terminal" and "GAME OVER" in app.turn.cget(
                "text"
            )
            result["checks"].append("terminal interface and resignation")
            app.destroy()
            app = None
        result["status"] = "pass"
        returncode = 0
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        returncode = 1
    finally:
        if app is not None:
            try:
                app.destroy()
            except Exception:
                pass
        report = os.environ.get("BGW_SMOKE_REPORT")
        if report:
            Path(report).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        print(json.dumps(result, ensure_ascii=False))
    return returncode


def main() -> None:
    if sys.argv[1:] == ["--native-self-test"]:
        sys.exit(native_self_test())
    run()


if __name__ == "__main__":
    main()
