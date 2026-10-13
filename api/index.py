"""Vercel's root-level ASGI entry point for the monorepo Python API."""

from server.app import app

__all__ = ["app"]
