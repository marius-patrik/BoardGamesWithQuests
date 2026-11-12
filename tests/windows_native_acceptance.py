"""External-input acceptance for the actual frozen Windows Tkinter desktop.

The driver is a separate process. It uses Windows mouse/keyboard events and
screen pixels; it never imports the application or invokes Tk widget methods.
A failed GUI journey fails CI and retains screenshot evidence for inspection.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
import traceback
from pathlib import Path

import pyautogui

DARK_SQUARE = (157, 146, 128)


def capture(output: Path, label: str):
    output.mkdir(parents=True, exist_ok=True)
    screenshot = pyautogui.screenshot().convert("RGB")
    screenshot.save(output / f"{label}.png")
    return screenshot


def _segments(counts: list[int], threshold: int) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(counts + [0]):
        if value >= threshold and start is None:
            start = index
        elif value < threshold and start is not None:
            if index - start >= 12:
                spans.append((start, index - 1))
            start = None
    return spans


def board_centers(screen) -> tuple[list[int], list[int]]:
    """Locate all eight grid rows/columns using rendered dark-square pixels."""
    width, height = screen.size
    xcount, ycount = [0] * width, [0] * height
    pixels = screen.load()
    for y in range(height):
        for x in range(width):
            color = pixels[x, y]
            if sum(abs(color[i] - DARK_SQUARE[i]) for i in range(3)) <= 18:
                xcount[x] += 1
                ycount[y] += 1
    xgroups = _segments(xcount, 22)
    ygroups = _segments(ycount, 22)
    if len(xgroups) != 8 or len(ygroups) != 8:
        raise AssertionError(
            f"Could not identify 8x8 rendered button board: columns={xgroups}, rows={ygroups}"
        )
    return (
        [(left + right) // 2 for left, right in xgroups],
        [(top + bottom) // 2 for top, bottom in ygroups],
    )


def wait_for_window(timeout: float = 35.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        candidates = [
            window
            for window in pyautogui.getWindowsWithTitle("BoardGamesWithQuests")
            if window.title.startswith("BoardGamesWithQuests")
        ]
        if candidates:
            window = candidates[0]
            window.restore() if window.isMinimized else None
            window.moveTo(5, 5)
            screen = pyautogui.size()
            window.resizeTo(min(990, screen.width - 20), min(735, screen.height - 65))
            window.activate()
            time.sleep(0.8)
            return window
        time.sleep(0.25)
    raise AssertionError("Frozen BoardGamesWithQuests window never became visible")


def wait_for_board(output: Path, label: str, timeout: float = 12.0):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        screen = capture(output, label)
        try:
            return board_centers(screen)
        except AssertionError as error:
            last_error = error
        time.sleep(0.4)
    raise AssertionError(f"The board never appeared after external input: {last_error}")


def stop_process_tree(process: subprocess.Popen | None) -> None:
    """Stop the PyInstaller bootloader and its GUI child before restarting."""
    if process is None:
        return
    if process.poll() is None:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            text=True,
            check=False,
        )
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if not any(
            w.title.startswith("BoardGamesWithQuests")
            for w in pyautogui.getWindowsWithTitle("BoardGamesWithQuests")
        ):
            return
        time.sleep(0.25)
    raise AssertionError("Prior frozen GUI remains open after process-tree termination")


def wait_for_named_window(title: str, timeout: float = 10) -> object:
    """Wait for an externally visible modal created by the frozen application."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        matches = [
            window for window in pyautogui.getWindowsWithTitle(title) if window.title == title
        ]
        if matches:
            return matches[0]
        time.sleep(0.2)
    raise AssertionError(f"Native user dialog never appeared: {title}")


def assert_dialog_closed(title: str) -> None:
    if any(window.title == title for window in pyautogui.getWindowsWithTitle(title)):
        raise AssertionError(f"Dialog remained open after external cancel: {title}")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def click_square(xs: list[int], ys: list[int], row: int, col: int) -> None:
    pyautogui.click(xs[col], ys[row])
    time.sleep(0.16)


def external_gameplay(exe: Path, evidence: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="bgw-win-native-") as temporary:
        data = Path(temporary)
        (data / "users.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "users": {
                        "alice": {"username": "alice", "display_name": "Alice", "xp": 0},
                        "bob": {"username": "bob", "display_name": "Bob", "xp": 0},
                    },
                }
            ),
            encoding="utf-8",
        )
        environment = dict(os.environ, BOARDGAMESWITHQUESTS_DATA_DIR=str(data))
        # Prove the frozen executable does not resolve Python from the host PATH.
        system_root = Path(os.environ.get("SystemRoot", r"C:\\Windows"))
        environment["PATH"] = os.pathsep.join(
            str(folder)
            for folder in (
                system_root / "System32",
                system_root,
                system_root / "System32" / "Wbem",
            )
        )
        for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
            environment.pop(name, None)
        report: dict = {"status": "failed", "checks": [], "platform": "Windows"}
        process = None
        try:
            process = subprocess.Popen([str(exe)], env=environment, cwd=str(data))
            wait_for_window()
            capture(evidence, "01-setup")
            # User keyboard event, not app-specific test hooks or widget.invoke().
            pyautogui.hotkey("ctrl", "enter", interval=0.12)
            xs, ys = wait_for_board(evidence, "02-board")
            report["checks"].append("real Windows window + external Ctrl+Enter match start")
            # White e2-e4, Black d7-d5, White e4xd5: capture quest +10 XP.
            for origin, destination in (
                ((6, 4), (4, 4)),
                ((1, 3), (3, 3)),
                ((4, 4), (3, 3)),
            ):
                click_square(xs, ys, *origin)
                click_square(xs, ys, *destination)
            capture(evidence, "03-capture-and-xp")
            logs = list((data / "logs").glob("*.json"))
            if len(logs) != 1:
                raise AssertionError(f"Expected exactly one persisted match: {logs}")
            history = read_json(logs[0])
            users = read_json(data / "users.json")
            assert len(history["events"]) == 3, history
            assert history["events"][-1]["capture"]["piece"] == "P", history
            assert history["events"][-1]["xp_awarded"] == 10, history
            assert users["users"]["alice"]["xp"] == 10, users
            report["checks"].append("external pointer moves + capture quest persisted to JSON")

            stop_process_tree(process)
            process = None
            process = subprocess.Popen([str(exe)], env=environment, cwd=str(data))
            wait_for_window()
            capture(evidence, "04-restarted-setup")
            # Actually create a local profile using the focused Tk entry fields.
            pyautogui.write("charlie", interval=0.06)
            pyautogui.press("tab")
            pyautogui.write("Charlie", interval=0.06)
            pyautogui.press("tab")
            pyautogui.press("space")
            time.sleep(0.6)
            capture(evidence, "05-created-profile")
            assert "charlie" in read_json(data / "users.json")["users"]
            report["checks"].append("external keyboard profile creation saved to JSON")
            pyautogui.hotkey("ctrl", "enter", interval=0.12)
            wait_for_board(evidence, "06-restarted-match")
            assert read_json(data / "users.json")["users"]["alice"]["xp"] == 10
            assert len(list((data / "logs").glob("*.json"))) == 2
            report["checks"].append("relaunch retained profile XP and created independent match")

            # Reach a capture-promotion entirely from the normal starting setup.
            # White: a2-a4, a4xb5, b5xa6, a6-a7, a7xb8=R.
            # Black: b7-b5, a7-a6, e7-e6, e6-e5.
            for origin, destination in (
                ((6, 0), (4, 0)),
                ((1, 1), (3, 1)),
                ((4, 0), (3, 1)),
                ((1, 0), (2, 0)),
                ((3, 1), (2, 0)),
                ((1, 4), (2, 4)),
                ((2, 0), (1, 0)),
                ((2, 4), (3, 4)),
            ):
                click_square(xs, ys, *origin)
                click_square(xs, ys, *destination)
            new_log = max((data / "logs").glob("*.json"), key=lambda file: file.stat().st_mtime_ns)
            assert len(read_json(new_log)["events"]) == 8

            click_square(xs, ys, 1, 0)
            click_square(xs, ys, 0, 1)
            wait_for_named_window("Pawn promotion")
            capture(evidence, "07-promotion-dialog")
            assert len(read_json(new_log)["events"]) == 8, "Unconfirmed promotion committed a move"
            pyautogui.press("esc")
            time.sleep(0.3)
            assert_dialog_closed("Pawn promotion")
            assert len(read_json(new_log)["events"]) == 8, "Cancelling promotion committed a move"
            report["checks"].append("real pointer promotion modal + external Escape cancellation")

            click_square(xs, ys, 1, 0)
            click_square(xs, ys, 0, 1)
            wait_for_named_window("Pawn promotion")
            # A Tk Toplevel starts with dialog focus; Tab traverses to Queen, then Rook.
            pyautogui.press("tab")
            pyautogui.press("tab")
            pyautogui.press("space")
            time.sleep(0.5)
            assert_dialog_closed("Pawn promotion")
            final_history = read_json(new_log)
            assert len(final_history["events"]) == 9
            assert final_history["events"][-1]["promotion"] == "R"
            assert final_history["events"][-1]["capture"]["piece"] == "N"
            assert {"capture", "promotion"}.issubset(
                set(final_history["events"][-1]["matched_rule_ids"])
            )
            capture(evidence, "08-rook-capture-promotion")
            report["checks"].append("real keyboard choice commits one capture promotion")

            # The same confirmation is reachable from the user's Ctrl+R shortcut.
            pyautogui.hotkey("ctrl", "r", interval=0.10)
            wait_for_named_window("Confirm resignation")
            pyautogui.press("enter")
            time.sleep(0.5)
            finished_history = read_json(new_log)
            assert len(finished_history["events"]) == 10
            assert finished_history["events"][-1]["type"] == "resignation"
            assert finished_history["status"] == "terminal"
            capture(evidence, "09-resigned-match")
            report["checks"].append("external keyboard resignation and terminal JSON result")
            report["status"] = "passed"
        except Exception as error:
            report["error"] = f"{type(error).__name__}: {error}"
            report["traceback"] = traceback.format_exc()
            capture(evidence, "failure")
            raise
        finally:
            stop_process_tree(process)
            (evidence / "external-acceptance.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
        return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, default=Path("native-evidence"))
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    if os.name != "nt":
        raise SystemExit("External Windows acceptance requires an interactive Windows desktop")
    pyautogui.FAILSAFE = True
    print(json.dumps(external_gameplay(exe, args.evidence.resolve()), indent=2))


if __name__ == "__main__":
    main()
