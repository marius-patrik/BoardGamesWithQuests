# Upstream Base & Fork Comparison Note

## Upstream Base Reference

This repository is a fork of the class project base:

- **Upstream Repository**: `https://github.com/docekalgjkt/ChessWithQuests`
- **Upstream Base Commit**: `a98e36d` (`docekalgjkt/ChessWithQuests:main`)

The `upstream` git remote is configured to that repository, so the base commit
is reachable without cloning anything separately.

> **Superseded 2026-10-02.** An earlier version of this note described a
> permanently pinned, branch-protected `upstream-base` branch and documented
> `git diff origin/upstream-base...main` as the way to inspect the fork diff.
> **That branch no longer exists** — it was deleted and pruned from the remote,
> so the documented command failed and the described protection was fiction. The
> remote-based commands below replace it.

## Comparing Against The Fork Base

The base commit is reachable through the `upstream` remote:

- **Web Diff URL**:
  `https://github.com/docekalgjkt/ChessWithQuests/compare/a98e36d...marius-patrik:ChessWithQuests:main`
- **CLI Diff**:
  `git fetch upstream && git diff a98e36d...main`

`git fetch upstream` ensures the remote-tracking ref for `a98e36d` is current
before diffing.

## Related

- `README.md` records the fork provenance in the project overview.
- `tests/test_upstream_base_notes.py` asserts that this note exists and mentions
  the base commit.
