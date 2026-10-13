"""ASGI entry point for Vercel, resolving monorepo packages without site customization."""

from pathlib import Path
import sys

PACKAGES = Path(__file__).resolve().parents[1] / "packages"
if str(PACKAGES) not in sys.path:
    sys.path.insert(0, str(PACKAGES))

from server.app import app

__all__ = ["app"]
