#!/usr/bin/env python3
"""Acceptance of extracted frozen applications, using native screen and pointer input."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
import zipfile

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)


class Blocked(RuntimeError):
    """An actual interactive graphical session is unavailable or an acceptance gate is unimplemented."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract(archive: Path, destination: Path) -> None:
    destination.mkdir()
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as source:
            for entry in source.infolist():
                if (
                    not (destination / entry.filename)
                    .resolve()
                    .is_relative_to(destination.resolve())
                ):
                    raise ValueError(f"archive path traversal: {entry.filename}")
                if ((entry.external_attr >> 16) & 0o170000) == 0o120000:
                    raise ValueError(f"zip symlink is forbidden: {entry.filename}")
            source.extractall(destination)
    else:
        # Python 3.12 data filter rejects traversal, dangerous links and special files.
        with tarfile.open(archive, "r:gz") as source:
            source.extractall(destination, filter="data")


def binary_architecture(exe: Path, target: str) -> str:
    with exe.open("rb") as stream:
        data = stream.read(4096)
    if target == "windows-x64":
        if data[:2] != b"MZ":
            raise ValueError("frozen Windows launcher is not PE")
        offset = struct.unpack_from("<I", data, 0x3C)[0]
        if data[offset : offset + 4] != b"PE\x00\x00":
            raise ValueError("invalid PE header")
        arch, expected = struct.unpack_from("<H", data, offset + 4)[0], 0x8664
    elif target.startswith("macos"):
        if data[:4] != b"\xcf\xfa\xed\xfe":
            raise ValueError("frozen macOS launcher is not thin Mach-O 64-bit")
        arch = struct.unpack_from("<I", data, 4)[0]
        expected = 0x0100000C if target == "macos-arm64" else 0x01000007
    else:
        if data[:4] != b"\x7fELF" or data[4:6] != b"\x02\x01":
            raise ValueError("frozen Linux launcher is not ELF64 little-endian")
        arch, expected = struct.unpack_from("<H", data, 18)[0], 62
    if arch != expected:
        raise ValueError(f"frozen binary architecture mismatch: {arch:#x} != {expected:#x}")
    return f"{arch:#x}"


def inspect_archive(args: argparse.Namespace, output: Path) -> tuple[Path, dict]:
    ext = ".zip" if args.platform.startswith("windows") else ".tar.gz"
    archive = args.release_dir / f"BoardGamesWithQuests-{args.version}-{args.platform}{ext}"
    sidecar = archive.with_name(archive.name + ".sha256")
    digest = sha256(archive)
    if sidecar.read_text(encoding="utf-8") != f"{digest}  {archive.name}\n":
        raise ValueError("the SHA256 sidecar differs from the actual release archive")
    extract(archive, output)
    bundle = output / (
        "BoardGamesWithQuests.app" if args.platform.startswith("macos") else "BoardGamesWithQuests"
    )
    if args.platform.startswith("macos"):
        exe = bundle / "Contents/MacOS/BoardGamesWithQuests"
        games = bundle / "Contents/Resources/games"
        manifest = bundle / "Contents/Resources/build-info.json"
    else:
        exe = bundle / (
            "BoardGamesWithQuests.exe"
            if args.platform.startswith("windows")
            else "BoardGamesWithQuests"
        )
        games = bundle / "_internal/games"
        manifest = bundle / "build-info.json"
    if not exe.is_file() or not manifest.is_file():
        raise ValueError("the extracted frozen launcher or its build identity is missing")
    info = json.loads(manifest.read_text(encoding="utf-8"))
    for key, expected in (
        ("source_sha", args.source_sha),
        ("platform", args.platform),
        ("release_version", args.version),
        ("pyinstaller_version", "6.16.0"),
    ):
        if info.get(key) != expected:
            raise ValueError(f"frozen manifest mismatch: {key}: {info.get(key)!r} != {expected!r}")
    if not str(info.get("python_version", "")).startswith("3.12."):
        raise ValueError("frozen application was not built with configured Python 3.12")
    resources = info.get("resources")
    if not isinstance(resources, dict) or not {
        "chess/config.json",
        "checkers/config.json",
    }.issubset(resources):
        raise ValueError("required bundled game JSON is not in the manifest")
    actual = {
        path.relative_to(games).as_posix(): sha256(path)
        for path in games.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    integrity = json.loads((games / "manifest.json").read_text(encoding="utf-8"))
    if integrity != {"version": 1, "files": resources}:
        raise ValueError("frozen integrity manifest differs from independently hashed resources")
    if resources != actual:
        raise ValueError("extracted bundled runtime data differs from the source build manifest")
    info.update(
        archive_name=archive.name,
        archive_sha256=digest,
        executable=str(exe),
        executable_architecture=binary_architecture(exe, args.platform),
    )
    return exe, info


def assert_native_runner(target: str) -> None:
    system, machine = platform.system().lower(), platform.machine().lower()
    required = {
        "windows-x64": ("windows", ("amd64", "x86_64")),
        "macos-arm64": ("darwin", ("arm64",)),
        "macos-x64": ("darwin", ("x86_64",)),
        "linux-x64": ("linux", ("x86_64",)),
    }
    os_name, archs = required[target]
    if system != os_name or machine not in archs:
        raise Blocked(f"incorrect native runner: {system}/{machine} expected {target}")


def corrupt_asset_check(executable: Path, target: str, cwd: Path) -> dict:
    """Prove the *extracted* frozen binary rejects altered bundled game JSON."""
    if target.startswith("macos"):
        games = executable.parent.parent / "Resources" / "games"
    else:
        games = executable.parent / "_internal" / "games"
    asset = games / "chess" / "config.json"
    original = asset.read_bytes()
    try:
        asset.write_bytes(b'{"corrupt":')
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [str(executable), "--check"],
            cwd=cwd,
            env=env,
            capture_output=True,
            timeout=90,
        )
        if result.returncode == 0:
            raise AssertionError("corrupt bundled Chess JSON was accepted by frozen application")
        bad_exit = result.returncode
    finally:
        asset.write_bytes(original)
    if asset.read_bytes() != original:
        raise AssertionError("extracted asset mutation was not fully restored")
    return {"corrupt_frozen_asset_rejected": True, "rejection_exit_code": bad_exit}


def missing_asset_check(executable: Path, target: str, cwd: Path) -> dict:
    """Removing a shipped ruleset must make the real frozen diagnostic fail."""
    games = (
        executable.parent.parent / "Resources" / "games"
        if target.startswith("macos")
        else executable.parent / "_internal" / "games"
    )
    asset = games / "checkers" / "config.json"
    original = asset.read_bytes()
    try:
        asset.unlink()
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [str(executable), "--check"],
            cwd=cwd,
            env=env,
            capture_output=True,
            timeout=90,
        )
        if result.returncode == 0:
            raise AssertionError("missing frozen Draughts JSON was accepted")
        return {"missing_frozen_asset_rejected": True, "rejection_exit_code": result.returncode}
    finally:
        asset.write_bytes(original)


def native_driver():
    try:
        import pyautogui

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.25
        image = pyautogui.screenshot()
        if image.width < 840 or image.height < 640:
            raise Blocked(f"interactive screen capture unavailable ({image.size})")
        return pyautogui
    except Blocked:
        raise
    except Exception as exc:
        raise Blocked(f"native screenshot/input unavailable: {exc}") from exc


def focus_chooser() -> None:
    if sys.platform.startswith("linux"):
        try:
            windows = subprocess.check_output(
                ["xdotool", "search", "--name", "^New game$"], text=True, timeout=5
            ).splitlines()
            if not windows:
                raise RuntimeError("game chooser not found")
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", windows[-1]], check=True, timeout=10
            )
        except Exception as exc:
            raise Blocked(f"X11 input/window activation unavailable: {exc}") from exc
    elif sys.platform == "darwin":
        script = (
            'tell application "System Events" to set frontmost of first process '
            'whose name contains "BoardGamesWithQuests" to true'
        )
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=15
        )
        if result.returncode:
            raise Blocked(f"macOS WindowServer/Accessibility permission: {result.stderr}")
    else:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        handles = []
        callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def inspect(hwnd, _):
            buffer = ctypes.create_unicode_buffer(user32.GetWindowTextLengthW(hwnd) + 1)
            user32.GetWindowTextW(hwnd, buffer, len(buffer))
            if "New game" in buffer.value and user32.IsWindowVisible(hwnd):
                handles.append(hwnd)
            return True

        active_callback = callback(inspect)
        user32.EnumWindows(active_callback, 0)
        if not handles or not user32.SetForegroundWindow(handles[-1]):
            raise Blocked("Windows runner has no foreground interactive desktop")


def visible_board(image) -> tuple[float, float, float]:
    """Identify the contiguous 8x8 checkerboard, not stray UI/dock colors."""
    palettes = (
        ((240, 217, 181), (181, 136, 99)),  # Chess
        ((232, 218, 188), (112, 87, 63)),  # English Draughts
    )
    picture = image.convert("RGB")
    pixels = picture.load()
    stride = 4
    failures: list[str] = []
    for light, dark in palettes:
        x_hits = [0] * picture.width
        y_hits = [0] * picture.height
        for y in range(0, picture.height, stride):
            for x in range(0, picture.width, stride):
                rgb = pixels[x, y]
                if min(
                    max(abs(rgb[i] - shade[i]) for i in range(3))
                    for shade in (light, dark)
                ) <= 7:
                    x_hits[x] += 1
                    y_hits[y] += 1
        if max(x_hits, default=0) < 20 or max(y_hits, default=0) < 20:
            failures.append("insufficient sample density")
            continue
        x_limit = max(20, int(max(x_hits) * 0.4))
        y_limit = max(20, int(max(y_hits) * 0.4))
        columns = [x for x in range(0, picture.width, stride) if x_hits[x] >= x_limit]
        rows = [y for y in range(0, picture.height, stride) if y_hits[y] >= y_limit]
        if not columns or not rows:
            failures.append("no concentrated checkerboard region")
            continue
        left, top = min(columns), min(rows)
        horizontal, vertical = max(columns) - left + stride, max(rows) - top + stride
        if abs(horizontal - vertical) > 16 or not 255 <= horizontal <= 710:
            failures.append(f"unexpected rectangle {horizontal}x{vertical}")
            continue
        square = (horizontal + vertical) / 16
        try:
            for row, col in ((3, 0), (3, 7), (4, 0), (4, 7)):
                x, y = int(left + (col + 0.22) * square), int(top + (row + 0.22) * square)
                expected = light if (row + col) % 2 == 0 else dark
                if max(abs(pixels[x, y][i] - expected[i]) for i in range(3)) > 25:
                    raise AssertionError(f"unexpected checker color at {row}, {col}")
        except (AssertionError, IndexError) as exc:
            failures.append(str(exc))
            continue
        return left, top, square
    raise AssertionError("no unobscured board Canvas: " + "; ".join(failures))


def await_board(gui, evidence: Path, label: str, timeout: float = 30) -> tuple[float, float, float]:
    deadline = time.monotonic() + timeout
    reason = ""
    while time.monotonic() < deadline:
        try:
            picture = gui.screenshot()
            board = visible_board(picture)
            picture.save(evidence / f"{label}.png")
            return board
        except Exception as exc:
            reason = str(exc)
        time.sleep(0.6)
    gui.screenshot().save(evidence / f"{label}-missing.png")
    raise AssertionError(f"frozen application did not render the game Canvas: {reason}")


def pointer_gameplay(gui, executable: Path, home: Path, evidence: Path, game: str) -> dict:
    home.mkdir()
    # macOS TemporaryDirectory may live below /var -> /private/var symlink.
    # The production preference security policy correctly rejects such a HOME.
    home = home.resolve()
    (home / "AppData" / "Roaming").mkdir(parents=True)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / ".config"),
        APPDATA=str(home / "AppData" / "Roaming"),
        USERPROFILE=str(home),
    )
    with tempfile.TemporaryDirectory(prefix="bgwq-external-cwd-") as cwd:
        with (evidence / f"{game}-stderr.txt").open("wb") as stderr:
            process = subprocess.Popen(
                [str(executable), "--game", game],
                cwd=cwd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=stderr,
            )
            try:
                limit = time.monotonic() + 25
                while time.monotonic() < limit:
                    if process.poll() is not None:
                        raise AssertionError(
                            f"frozen executable exited at startup: {process.returncode}"
                        )
                    try:
                        focus_chooser()
                        break
                    except Blocked:
                        time.sleep(0.5)
                else:
                    raise Blocked("could not access the real frozen New game chooser")
                gui.sleep(0.8)
                gui.screenshot().save(evidence / f"{game}-chooser.png")
                # Native window coordinates are measured on each runner.
                # Click the visible Start control; do not infer modal Tab order.
                try:
                    x, y, width, height = native_window_rectangle("New game")
                    gui.click(x + 0.34 * width, y + 0.66 * height)
                    left, top, size = await_board(gui, evidence, f"{game}-opening", timeout=7)
                except (AssertionError, Blocked) as error:
                    last_error = error
                else:
                    last_error = None
                # Fall back to the known native chooser keyboard interaction only
                # when the pointer-controlled route did not produce the real board.
                if last_error is not None:
                    focus_chooser()

                for attempt in range(4) if last_error is not None else range(0):
                    gui.press("tab")
                    gui.press("return")
                    try:
                        left, top, size = await_board(gui, evidence, f"{game}-opening", timeout=5)
                        break
                    except AssertionError as error:
                        last_error = error
                        gui.screenshot().save(
                            evidence / f"{game}-chooser-attempt-{attempt + 1}.png"
                        )
                else:
                    if last_error is not None:
                        raise AssertionError(
                            f"native game chooser did not accept Start: {last_error}"
                        )
                start, end = ((6, 4), (5, 4)) if game == "chess" else ((2, 1), (3, 0))

                def square(position):
                    return (
                        left + (position[1] + 0.5) * size,
                        top + (position[0] + 0.5) * size,
                    )

                gui.click(*square(start))
                gui.sleep(0.5)
                gui.screenshot().save(evidence / f"{game}-selected.png")
                gui.click(*square(end))
                gui.sleep(0.8)
                after = gui.screenshot()
                after.save(evidence / f"{game}-move.png")
                from PIL import Image, ImageChops

                before = Image.open(evidence / f"{game}-opening.png").convert("RGB")
                changes = ImageChops.difference(before, after.convert("RGB"))
                radius = max(9, int(size * 0.22))
                for position in (start, end):
                    x, y = square(position)
                    box = (
                        int(x) - radius,
                        int(y) - radius,
                        int(x) + radius,
                        int(y) + radius,
                    )
                    if not changes.crop(box).getbbox():
                        raise AssertionError(
                            f"{game} pointer move did not visibly change piece at {position}"
                        )
                if process.poll() is not None:
                    raise AssertionError(f"{game} frozen process unexpectedly terminated")
                gui.hotkey("command", "q") if sys.platform == "darwin" else gui.hotkey("alt", "f4")
                try:
                    result = process.wait(timeout=12)
                except subprocess.TimeoutExpired as exc:
                    raise AssertionError("native close action did not exit frozen app") from exc
                if result:
                    raise AssertionError(f"frozen GUI exit status: {result}")
                return {
                    "actual_chooser": True,
                    "initial_board": True,
                    "real_pointer_move": True,
                    "observed_piece_change": True,
                    "native_window_close": True,
                }
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=8)


def native_window_rectangle(title: str) -> tuple[int, int, int, int]:
    """Locate an actual OS-owned Tk toplevel; no source-process introspection."""
    if sys.platform.startswith("linux"):
        windows = subprocess.check_output(
            ["xdotool", "search", "--name", f"^{title}$"], text=True, timeout=8
        ).splitlines()
        if not windows:
            raise AssertionError(f"native dialog not found: {title}")
        geometry = subprocess.check_output(
            ["xdotool", "getwindowgeometry", "--shell", windows[-1]],
            text=True,
            timeout=8,
        )
        values = dict(line.split("=", 1) for line in geometry.splitlines() if "=" in line)
        x, y, width, height = (int(values[key]) for key in ("X", "Y", "WIDTH", "HEIGHT"))
        # This pinned Openbox/Xvfb runner exposes Tk child bounds, not
        # the decorated Settings window. Verified against actual screenshots.
        x, y, width, height = x - 28, y - 55, width - 10, height + 15
    elif sys.platform == "darwin":
        import re

        code = (
            'tell application "System Events"\n'
            'set p to first process whose name contains "BoardGamesWithQuests"\n'
            "tell p\n"
            'set w to first window whose name is "' + title + '"\n'
            "get {position of w, size of w}\n"
            "end tell\n"
            "end tell"
        )
        result = subprocess.run(
            ["osascript", "-e", code], capture_output=True, text=True, timeout=15
        )
        if result.returncode:
            raise Blocked(
                f"macOS Accessibility does not expose the native {title!r} dialog: "
                + result.stderr.strip()
            )
        numbers = [int(value) for value in re.findall(r"-?\d+", result.stdout)]
        if len(numbers) != 4:
            raise Blocked(f"unexpected AppKit dialog geometry: {result.stdout!r}")
        x, y, width, height = numbers
    else:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        windows = []
        callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def inspect(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            buffer = ctypes.create_unicode_buffer(user32.GetWindowTextLengthW(hwnd) + 1)
            user32.GetWindowTextW(hwnd, buffer, len(buffer))
            if buffer.value == title:
                windows.append(hwnd)
            return True

        enum_callback = callback(inspect)
        user32.EnumWindows(enum_callback, 0)
        if not windows:
            raise AssertionError(f"Windows native dialog not found: {title}")
        rect = wintypes.RECT()
        if not user32.GetWindowRect(windows[-1], ctypes.byref(rect)):
            raise Blocked(f"Windows GetWindowRect failed for {title}")
        x, y, width, height = (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
    if not 150 < width < 900 or not 130 < height < 600:
        raise AssertionError(f"implausible native {title} dialog: {(x, y, width, height)}")
    return x, y, width, height


def screenshot_dialog(gui, evidence: Path, label: str, title: str):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        try:
            rect = native_window_rectangle(title)
            gui.screenshot().save(evidence / f"{label}.png")
            (evidence / f"{label}-rectangle.json").write_text(
                json.dumps({"x": rect[0], "y": rect[1], "width": rect[2], "height": rect[3]})
                + "\n",
                encoding="utf-8",
            )
            return rect
        except AssertionError:
            gui.sleep(0.4)
    gui.screenshot().save(evidence / f"{label}-missing.png")
    raise AssertionError(f"{title} native dialog did not render within 12 seconds")


def settings_button(board: tuple[float, float, float], target: str) -> tuple[float, float]:
    left, top, size = board
    # Measured against native Tk screenshots, never source widget commands.
    offsets = {
        "windows-x64": (13.2, -2.95),
        "macos-arm64": (12.45, -2.75),
        "macos-x64": (12.49, -2.75),
        "linux-x64": (12.56, -3.52),
    }
    dx, dy = offsets[target]
    return left + dx * size, top + dy * size


def preferences_file(home: Path) -> Path:
    if sys.platform.startswith("win"):
        return home / "AppData" / "Roaming" / "BoardGamesWithQuests" / "preferences.json"
    if sys.platform == "darwin":
        return (
            home / "Library" / "Application Support" / "BoardGamesWithQuests" / "preferences.json"
        )
    return home / ".config" / "BoardGamesWithQuests" / "preferences.json"


def settings_journey(gui, exe: Path, home: Path, evidence: Path, platform_name: str) -> dict:
    """Exercise Cancel, Save and restart from actual native dialogs and OS user data."""
    home.mkdir()
    # macOS TemporaryDirectory may live below /var -> /private/var symlink.
    # The production preference security policy correctly rejects such a HOME.
    home = home.resolve()
    (home / "AppData" / "Roaming").mkdir(parents=True)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.update(
        HOME=str(home),
        USERPROFILE=str(home),
        APPDATA=str(home / "AppData" / "Roaming"),
        XDG_CONFIG_HOME=str(home / ".config"),
    )
    path = preferences_file(home)

    def open_chooser_settings() -> None:
        limit = time.monotonic() + 25
        while time.monotonic() < limit:
            try:
                focus_chooser()
                break
            except Blocked:
                gui.sleep(0.5)
        else:
            raise Blocked("native chooser not focused for settings")
        gui.sleep(0.5)
        gui.screenshot().save(evidence / "settings-chooser.png")
        # ModalLifecycle activates the readonly game selector. Tab order:
        # selector -> Start -> Settings; Enter activates the focused button.
        if sys.platform.startswith("linux"):
            # X11 keeps the combobox keyboard traversal deterministic, whereas
            # decorated-window geometry includes window-manager offsets.
            gui.press("tab")
            gui.press("tab")
            gui.press("return")
        else:
            x, y, width, height = native_window_rectangle("New game")
            (evidence / "chooser-hit-target.json").write_text(
                json.dumps({"rect": [x, y, width, height],
                            "point": [x + 0.66 * width, y + 0.66 * height]}) + "\n",
                encoding="utf-8",
            )
            gui.click(x + 0.66 * width, y + 0.66 * height)
        screenshot_dialog(gui, evidence, "settings-dialog", "Settings")

    def edit_settings() -> None:
        # SettingsDialog activates its Spinbox, regardless of the window position.
        gui.hotkey("command", "a") if sys.platform == "darwin" else gui.hotkey("ctrl", "a")
        gui.write("64", interval=0.08)
        gui.press("tab")
        gui.press("space")
        gui.screenshot().save(evidence / "settings-edited.png")

    for cycle in (0, 1):
        with tempfile.TemporaryDirectory(prefix="bgwq-settings-outside-") as cwd:
            with (evidence / f"settings-cycle-{cycle}-stderr.txt").open("wb") as stderr:
                process = subprocess.Popen(
                    [str(exe), "--game", "chess"],
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=stderr,
                )
                try:
                    open_chooser_settings()
                    if cycle == 0:
                        edit_settings()
                        # Escape is bound to cancel, and must not create user settings.
                        gui.press("escape")
                        if path.exists():
                            raise AssertionError(
                                "Settings Cancel unexpectedly persisted preferences"
                            )
                        open_chooser_settings()
                        edit_settings()
                        # SettingsDialog binds Return to Save on the actual Toplevel.
                        gui.press("return")
                        deadline = time.monotonic() + 10
                        while time.monotonic() < deadline and not path.is_file():
                            gui.sleep(0.3)
                        if not path.is_file():
                            gui.screenshot().save(evidence / "settings-save-missing.png")
                            raise AssertionError(f"native Settings Save did not persist: {path}")
                        expected = {"board_size": 64, "show_coordinates": False}
                        saved = json.loads(path.read_text(encoding="utf-8"))
                        if saved != expected:
                            gui.screenshot().save(evidence / "settings-save-wrong.png")
                            raise AssertionError(f"unexpected persisted settings: {saved!r}")
                        gui.screenshot().save(evidence / "settings-save-complete.png")
                    else:
                        if json.loads(path.read_text(encoding="utf-8")) != {
                            "board_size": 64,
                            "show_coordinates": False,
                        }:
                            raise AssertionError(
                                "preferences were lost across native process restart"
                            )
                        gui.screenshot().save(evidence / "settings-after-process-restart.png")
                        gui.press("escape")
                    # Dismiss the still-open initial New game modal; verify real board.
                    focus_chooser()
                    gui.press("escape")
                    await_board(gui, evidence, f"settings-board-{cycle}")
                    (
                        gui.hotkey("command", "q")
                        if sys.platform == "darwin"
                        else gui.hotkey("alt", "f4")
                    )
                    if process.wait(timeout=15) != 0:
                        raise AssertionError("frozen GUI did not exit cleanly after settings")
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=8)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=8)
    return {
        "settings_cancel_no_write": True,
        "settings_saved_from_real_dialog": True,
        "process_restart": True,
        "settings_persisted": True,
        "user_config_path": str(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform",
        required=True,
        choices=(
            "windows-x64",
            "macos-arm64",
            "macos-x64",
            "linux-x64",
        ),
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--release-dir", type=Path, default=Path("dist/release"))
    parser.add_argument("--evidence-dir", type=Path, default=Path("dist/native-evidence"))
    args = parser.parse_args()
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "platform": args.platform,
        "source_sha": args.source_sha,
        "host_os": platform.platform(),
        "host_machine": platform.machine(),
        "python": sys.version.split()[0],
        "packaging": "NOT_RUN",
        "gui": "NOT_RUN",
        "classification": "FAIL",
        "games": {},
        "remaining_final_head_gates": [
            "real save/restart/reopen with history and active side",
            "in-app switching and cancellation",
            "resignation and terminal reset",
            "draughts capture and promotion variants",
            "signed Windows binary and notarized macOS app",
            "complete Chess/Draughts native capture, promotion and terminal journeys",
            "clean subprocess-tree lifecycle and offline execution",
        ],
    }
    try:
        assert_native_runner(args.platform)
        with tempfile.TemporaryDirectory(prefix="bgwq-native-") as scratch:
            folder = Path(scratch)
            executable, manifest = inspect_archive(args, folder / "extracted")
            state["packaging"] = "PASS"
            state["metadata"] = manifest
            env = dict(os.environ)
            env.pop("PYTHONPATH", None)
            check = subprocess.run(
                [str(executable), "--check"],
                cwd=folder,
                env=env,
                capture_output=True,
                timeout=100,
            )
            state["frozen_check_exit_code"] = check.returncode
            if check.returncode:
                raise AssertionError(
                    f"frozen diagnostic failed: {check.stderr.decode(errors='replace')}"
                )
            state["corrupt_asset"] = corrupt_asset_check(executable, args.platform, folder)
            state["missing_asset"] = missing_asset_check(executable, args.platform, folder)
            gui = native_driver()
            for game in ("chess", "checkers"):
                state["games"][game] = pointer_gameplay(
                    gui, executable, folder / f"home-{game}", args.evidence_dir, game
                )
            state["settings"] = settings_journey(
                gui, executable, folder / "home-settings", args.evidence_dir, args.platform
            )
            state["gui"] = "PARTIAL"
            # Incomplete mandatory journeys are BLOCKED, never a green release gate.
            raise Blocked("extracted gameplay was exercised but final native journeys remain")
    except Blocked as error:
        state.update(classification="BLOCKED", reason=str(error))
        exit_code = 2
    except Exception as error:
        state.update(
            classification="FAIL",
            reason=str(error),
            traceback=traceback.format_exc(),
        )
        exit_code = 1
    finally:
        report = args.evidence_dir / "native-result.json"
        report.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "classification": state["classification"],
                    "platform": args.platform,
                    "reason": state.get("reason"),
                    "report": str(report),
                }
            ),
            flush=True,
        )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
