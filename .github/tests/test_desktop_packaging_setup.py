"""Phase 0 verification of the packaged desktop release integration."""

from __future__ import annotations

import hashlib
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

    def test_release_is_gated_on_real_platform_artifacts(self) -> None:
        release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        desktop = (ROOT / ".github/workflows/desktop-build.yml").read_text(encoding="utf-8")
        self.assertIn("needs: [prepare, packages]", release)
        self.assertIn("uses: ./.github/workflows/desktop-build.yml", release)
        self.assertIn("merge-multiple: true", release)
        self.assertIn("name: release-notes", release)
        self.assertNotIn("name: desktop-release-notes", release)
        self.assertIn("sha256sum --check", release)
        self.assertIn("--draft", release)
        self.assertIn("--draft=false", release)
        for platform in ("windows-x64", "macos-arm64", "macos-x64", "linux-x64"):
            self.assertIn(platform, release)
            self.assertIn(platform, desktop)
        self.assertIn("Package and smoke-test the frozen GUI", desktop)
        self.assertIn("SETUPTOOLS_SCM_PRETEND_VERSION", desktop)


if __name__ == "__main__":
    unittest.main()
