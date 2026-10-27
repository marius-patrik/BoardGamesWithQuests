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
        if path.is_file()
    }
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


def native_driver():
    try:
        import pyautogui

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.25
        image = pyautogui.screenshot()
        if image.width < 840 or image.height < 640 or not image.getbbox():
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
    pixels = image.convert("RGB").load()
    xs, ys = [], []
    for y in range(0, image.height, 4):
        for x in range(0, image.width, 4):
            rgb = pixels[x, y]
            if min(max(abs(rgb[i] - shade[i]) for i in range(3)) for shade in (LIGHT, DARK)) <= 7:
                xs.append(x)
                ys.append(y)
    if len(xs) < 3000:
        raise AssertionError(f"expected frozen Canvas, found only {len(xs)} colour samples")
    left, top = min(xs), min(ys)
    horizontal, vertical = max(xs) - left + 4, max(ys) - top + 4
    if abs(horizontal - vertical) > 16 or not 255 <= horizontal <= 710:
        raise AssertionError(f"board not an 8x8 square: {horizontal}x{vertical}")
    size = (horizontal + vertical) / 16
    for row, col in ((3, 0), (3, 7), (4, 0), (4, 7)):
        x, y = int(left + (col + 0.22) * size), int(top + (row + 0.22) * size)
        expected = LIGHT if (row + col) % 2 == 0 else DARK
        if max(abs(pixels[x, y][i] - expected[i]) for i in range(3)) > 25:
            raise AssertionError(f"board checker pattern invalid at ({row}, {col})")
    return left, top, size


def await_board(gui, evidence: Path, label: str) -> tuple[float, float, float]:
    deadline = time.monotonic() + 30
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
                gui.screenshot().save(evidence / f"{game}-chooser.png")
                gui.press("tab")
                gui.press("return")
                left, top, size = await_board(gui, evidence, f"{game}-opening")
                start, end = ((6, 4), (5, 4)) if game == "chess" else ((5, 0), (4, 1))

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
            "settings persistence across restart",
            "in-app switching and cancellation",
            "resignation and terminal reset",
            "draughts capture and promotion variants",
            "signed Windows binary and notarized macOS app",
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
            gui = native_driver()
            for game in ("chess", "checkers"):
                state["games"][game] = pointer_gameplay(
                    gui, executable, folder / f"home-{game}", args.evidence_dir, game
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
