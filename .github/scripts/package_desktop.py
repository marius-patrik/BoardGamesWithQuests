#!/usr/bin/env python3
"""Produce a checked, self-contained desktop archive from the Python/Tkinter app."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
import platform as host_platform
from pathlib import Path
import re
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
    checksum_hash = hashlib.sha256()
    with archive.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            checksum_hash.update(chunk)
    digest = checksum_hash.hexdigest()
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
    # Read the checked-out distribution identity on every supported Python.
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    resources = [
        path for path in games.rglob("*") if path.is_file() and "__pycache__" not in path.parts
    ]
    if not resources:
        raise FileNotFoundError("Desktop game runtime resources are empty")

    with (ROOT / "pyproject.toml").open("rb") as source:
        distribution = tomllib.load(source)["project"]["name"]
    dist = ROOT / "dist/desktop"
    work = ROOT / "build/pyinstaller"
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name",
        "BoardGamesWithQuests",
        "--paths",
        str(ROOT / "src"),
        "--add-data",
        f"{games}{os.pathsep}games",
        "--collect-submodules",
        "games",
        "--copy-metadata",
        distribution,
        "--distpath",
        str(dist),
        "--workpath",
        str(work),
        "--specpath",
        str(ROOT / "build"),
        str(entry),
    ]
    subprocess.run(args, cwd=ROOT, check=True)
    bundle = dist / (
        "BoardGamesWithQuests.app" if platform.startswith("macos") else "BoardGamesWithQuests"
    )
    runtime = bundle / (
        "Contents/Resources/games" if platform.startswith("macos") else "_internal/games"
    )
    for source in resources:
        packaged = runtime / source.relative_to(games)
        if not packaged.is_file() or packaged.read_bytes() != source.read_bytes():
            raise FileNotFoundError(f"Missing or altered frozen runtime resource: {packaged}")
    return bundle


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
    # A frozen application must load its actual embedded JSON rulebooks and
    # perform a real versioned game transition, idempotent retry and replay.
    # The --windowed Windows binary has no console; inspect its exit code.
    check = subprocess.run([str(executable), "--check"], cwd=ROOT, capture_output=True, timeout=90)
    if check.returncode != 0:
        raise RuntimeError(
            f"Frozen application game diagnostic failed ({check.returncode}): "
            + check.stderr.decode("utf-8", errors="replace")
        )
    command = [str(executable)]
    if platform == "linux-x64":
        command = ["xvfb-run", "-a", *command]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        time.sleep(5)
        if process.poll() is not None:
            error = (
                process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            )
            raise RuntimeError(
                f"Packaged GUI exited before smoke interval: {process.returncode}: {error}"
            )
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def write_build_identity(bundle: Path, platform: str, version: str) -> Path:
    """Bind the candidate archive to the actual checkout and bundled data."""
    source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("Invalid checked-out source identity")
    if os.environ.get("GITHUB_SHA") and os.environ["GITHUB_SHA"] != source_sha:
        raise ValueError("Source checkout is not the GitHub Actions source SHA")
    machine = host_platform.machine().lower()
    expected = {
        "windows-x64": ("amd64", "x86_64"),
        "macos-arm64": ("arm64",),
        "macos-x64": ("x86_64",),
        "linux-x64": ("x86_64",),
    }
    if machine not in expected[platform]:
        raise ValueError(f"Host architecture {machine} disagrees with {platform}")
    games = ROOT / "src/games"
    resources = {
        path.relative_to(games).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(games.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }
    if not {"chess/config.json", "checkers/config.json"}.issubset(resources):
        raise ValueError("Source checkout is missing required game JSON")
    record = {
        "source_sha": source_sha,
        "platform": platform,
        "release_version": version,
        "host_architecture": machine,
        "python_version": sys.version.split()[0],
        "pyinstaller_version": metadata.version("pyinstaller"),
        "resources": resources,
    }
    location = (
        bundle / "Contents/Resources/build-info.json"
        if platform.startswith("macos")
        else bundle / "build-info.json"
    )
    location.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return location


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    bundle = build(args.platform, args.version)
    smoke(bundle, args.platform)
    write_build_identity(bundle, args.platform, args.version)
    archive, checksum = archive_bundle(bundle, ROOT / "dist/release", args.platform, args.version)
    print(f"Verified desktop bundle: {bundle}")
    print(f"Release asset: {archive}")
    print(f"SHA256: {checksum}")


if __name__ == "__main__":
    main()
