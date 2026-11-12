"""src/model/user.py: declaration-only scaffold.

Actual gameplay, UI, storage and rule implementation is deliberately absent.
The approved behavior is specified in .agents/PRD.md.
"""

from __future__ import annotations


class Uzivatel:
    """TODO: implement this contract."""

    pass


class UserManager:
    """TODO: implement this contract."""

    @staticmethod
    def _fingerprint(*args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    @staticmethod
    def _read_profiles(*args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def nacti_uzivatele(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def _recover_for_retry(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def vytvor_uzivatele(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def pridej_xp(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")

    def uloz_uzivatele(self, *args, **kwargs):
        raise NotImplementedError("Scaffold only: see .agents/PRD.md")


def data_directory(*args, **kwargs):
    raise NotImplementedError("Scaffold only: see .agents/PRD.md")


def atomic_json(*args, **kwargs):
    raise NotImplementedError("Scaffold only: see .agents/PRD.md")


def profile_write_lock(*args, **kwargs):
    raise NotImplementedError("Scaffold only: see .agents/PRD.md")


def normalize_username(*args, **kwargs):
    raise NotImplementedError("Scaffold only: see .agents/PRD.md")
