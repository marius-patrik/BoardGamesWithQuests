#!/usr/bin/env python3
"""Produce a checked, self-contained desktop archive from the Python/Tkinter app."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile


ROOT = Path(__file__).resolve().parents[2]
PLATFORMS = {"windows-x64", "macos-arm64", "macos-x64", "linux-x64"}
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def archive_bundle(bundle: Path, output: Path, platform: str, version: str) -> tuple[Path, Path]:
    """Archive a verified bundle and write a matching SHA256 sidecar."""
    if platform not in PLATFORMS or not VERSION.fullmatch(version):
        raise ValueError("Unsupported platform or release version")
    if not bundle.exists():
        raise FileNotFoundError(bundle)
    output.mkdir(parents=True, exist_ok=True)
    stem = f"BoardGamesWithQuests-{version}-{platform}"
    if platform.startswith("windows"):
        archive = output / (stem + ".zip")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as dest:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    dest.write(path, arcname=(Path(bundle.name) / path.relative_to(bundle)))
    else:
        archive = output / (stem + ".tar.gz")
        with tarfile.open(archive, "w:gz") as dest:
            dest.add(bundle, arcname=bundle.name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = output / (archive.name + ".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive, checksum


def build(platform: str, version: str) -> Path:
    """Build the real desktop entry point and include dynamically loaded game sources."""
    if platform not in PLATFORMS or not VERSION.fullmatch(version):
        raise ValueError("A supported platform and PrideVer release version are required")
    entry = ROOT / "src/chesswithquests/__main__.py"
    games = ROOT / "src/games"
    if not entry.is_file() or not games.is_dir():
        raise FileNotFoundError("Completed desktop sources under src/ are required")
    dist = ROOT / "dist/desktop"
    work = ROOT / "build/pyinstaller"
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
        "--windowed", "--name", "BoardGamesWithQuests",
        "--paths", str(ROOT / "src"),
        "--add-data", f"{games}{os.pathsep}games",
        "--collect-submodules", "games",
        "--copy-metadata", "boardgameswithquests",
        "--distpath", str(dist), "--workpath", str(work),
        "--specpath", str(ROOT / "build"),
        str(entry),
    ]
    subprocess.run(args, cwd=ROOT, check=True)
    if platform.startswith("macos"):
        return dist / "BoardGamesWithQuests.app"
    return dist / "BoardGamesWithQuests"


def smoke(bundle: Path, platform: str) -> None:
    """Exercise the packaged GUI process, not a source-checkout Python interpreter."""
    if platform.startswith("macos"):
        executable = bundle / "Contents/MacOS/BoardGamesWithQuests"
    elif platform.startswith("windows"):
        executable = bundle / "BoardGamesWithQuests.exe"
    else:
        executable = bundle / "BoardGamesWithQuests"
    if not executable.is_file():
        raise FileNotFoundError(f"Frozen entry point missing: {executable}")
    command = [str(executable)]
    if platform == "linux-x64":
        command = ["xvfb-run", "-a", *command]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        time.sleep(5)
        if process.poll() is not None:
            error = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            raise RuntimeError(f"Packaged GUI exited before smoke interval: {process.returncode}: {error}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    bundle = build(args.platform, args.version)
    smoke(bundle, args.platform)
    archive, checksum = archive_bundle(
        bundle, ROOT / "dist/release", args.platform, args.version
    )
    print(f"Verified desktop bundle: {bundle}")
    print(f"Release asset: {archive}")
    print(f"SHA256: {checksum}")


if __name__ == "__main__":
    main()
