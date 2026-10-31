"""Phase 0 verification of the packaged desktop release integration."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]


class DesktopPackagingInfrastructureTests(unittest.TestCase):
    def test_archive_outputs_verified_sha256_for_each_supported_platform(self) -> None:
        script = ROOT / ".github/scripts/package_desktop.py"
        spec = importlib.util.spec_from_file_location("package_desktop", script)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "BoardGamesWithQuests"
            bundle.mkdir()
            (bundle / "example.txt").write_text("test package", encoding="utf-8")
            output = Path(tmp) / "release"
            archive, sidecar = module.archive_bundle(bundle, output, "windows-x64", "1.0.0")
            self.assertTrue(zipfile.is_zipfile(archive))
            self.assertEqual(
                sidecar.read_text(encoding="utf-8"),
                f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n",
            )
            self.assertIn("BoardGamesWithQuests/example.txt", zipfile.ZipFile(archive).namelist())
            for platform in ("macos-arm64", "macos-x64", "linux-x64"):
                package, checksum = module.archive_bundle(bundle, output, platform, "1.0.0")
                self.assertTrue(package.is_file())
                self.assertTrue(checksum.is_file())

    def test_bundler_output_requires_all_runtime_resources_and_actual_metadata(self) -> None:
        # Run the real helper and subprocess boundary; the external bundler fixture
        # models complete, missing and corrupt copy results without GUI source.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / ".github/scripts/package_desktop.py"
            script.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / ".github/scripts/package_desktop.py", script)
            (root / "src").mkdir(parents=True)
            (root / "src/boardgameswithquests.py").write_text("", encoding="utf-8")
            games = root / "games/chess"
            games.mkdir(parents=True)
            (games / "rules.py").write_text("runtime resource", encoding="utf-8")
            (root / "pyproject.toml").write_text(
                '[project]\nname = "fixture-distribution"\n', encoding="utf-8"
            )
            (root / "PyInstaller.py").write_text(
                "import os, pathlib, shutil, sys\n"
                "args = sys.argv[1:]\n"
                "assert args[args.index('--copy-metadata') + 1] == 'fixture-distribution'\n"
                "bundle = pathlib.Path(args[args.index('--distpath') + 1]) / 'BoardGamesWithQuests'\n"
                "runtime = bundle / '_internal/games'\n"
                "shutil.copytree('games', runtime, dirs_exist_ok=True)\n"
                "mode = os.environ['BUNDLER_RESULT']\n"
                "resource = runtime / 'chess/rules.py'\n"
                "if mode == 'missing': resource.unlink()\n"
                "if mode == 'corrupt': resource.write_text('wrong bytes')\n",
                encoding="utf-8",
            )
            command = [
                sys.executable,
                "-c",
                "import runpy; m = runpy.run_path('.github/scripts/package_desktop.py'); "
                "print(m['build']('linux-x64', '1.0.0'))",
            ]
            for mode in ("complete", "missing", "corrupt"):
                with self.subTest(mode=mode):
                    result = subprocess.run(
                        command,
                        cwd=root,
                        text=True,
                        capture_output=True,
                        env=dict(os.environ, BUNDLER_RESULT=mode),
                    )
                    if mode == "complete":
                        self.assertEqual(result.returncode, 0, result.stderr)
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("Missing or altered frozen runtime resource", result.stderr)

    def test_existing_public_and_draft_releases_are_never_reused(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        start = workflow.index('          if gh release view "$TAG"')
        end = workflow.index("          names=", start)
        import textwrap

        script = textwrap.dedent(workflow[start:end])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gh = root / "gh"
            gh.write_text(
                "#!/bin/sh\n"
                'echo "$*" >> "$CALL_LOG"\n'
                'if [ "$2" = view ]; then\n'
                '  [ "$RELEASE_STATE" != absent ] || exit 1\n'
                '  case "$*" in *--json*) echo "$RELEASE_STATE";; esac\n'
                "fi\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)
            for state in ("absent", "true", "false"):
                log = root / (state + ".log")
                result = subprocess.run(
                    ["bash", "-eu", "-c", script],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    env=dict(
                        os.environ,
                        PATH=str(root) + os.pathsep + os.environ["PATH"],
                        RELEASE_STATE=state,
                        CALL_LOG=str(log),
                        TAG="v1.0.0",
                        GITHUB_REPOSITORY="fixture/repo",
                        GITHUB_SHA="a" * 40,
                    ),
                )
                calls = log.read_text()
                if state == "absent":
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("release create", calls)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("release create", calls)
                    self.assertNotIn("release upload", calls)
                    self.assertNotIn("release edit", calls)

    def test_release_is_gated_on_real_platform_artifacts(self) -> None:
        release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        desktop = (ROOT / ".github/workflows/desktop-build.yml").read_text(encoding="utf-8")
        self.assertIn("needs: [prepare, packages]", release)
        self.assertIn("uses: ./.github/workflows/desktop-build.yml", release)
        self.assertIn("merge-multiple: true", release)
        self.assertIn("name: release-notes", release)
        self.assertNotIn("--clobber", release)
        self.assertIn("refusing to reuse stale draft assets", release)
        self.assertIn("Existing published release must be reviewed", release)
        self.assertNotIn("name: desktop-release-notes", release)
        self.assertIn("sha256sum --check", release)
        self.assertIn("--draft", release)
        self.assertIn("--draft=false", release)
        for platform in ("windows-x64", "macos-arm64", "macos-x64", "linux-x64"):
            self.assertIn(platform, release)
            self.assertIn(platform, desktop)
        self.assertIn("Package and smoke-test the frozen GUI", desktop)
        self.assertIn("SETUPTOOLS_SCM_PRETEND_VERSION", desktop)

    def test_packager_derives_metadata_from_the_checked_out_project(self) -> None:
        script = (ROOT / ".github/scripts/package_desktop.py").read_text(encoding="utf-8")
        self.assertIn('tomllib.load(source)["project"]["name"]', script)
        self.assertNotIn('"--copy-metadata",\n        "boardgameswithquests",', script)


if __name__ == "__main__":
    unittest.main()
