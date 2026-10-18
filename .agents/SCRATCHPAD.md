# Scratchpad — Current investigation

Temporary findings, not requirements or architectural decisions. Promote confirmed implementation facts to the appropriate `notes/`, `requests/` or `decisions/`; actions to [TODO](TODO.md). Delete resolved observations.

- **Current #414 source:** `packages/engine/` plus `packages/chess/config.json` and `packages/checkers/config.json`. Both game definitions say `playable: false`; the finished Tkinter view is only in downstream #271, not this branch.
- **Engine limitations:** `Board.setup_default_board` initializes standard chess on 8×8; `Move.validate` hardcodes 8×8 bounds; `GameManager.save_log()` is a no-op. Do not present this engine as a complete generic draughts implementation.
- **Packaging evidence:** #414 has the platform build matrix and a frozen-process smoke gate, but cannot run complete GUI acceptance until #271 contributes `src/`. Python release remains disabled.
- **Provider evidence:** GitHub protection administration currently returns HTTP 403 for this integration. `main` protection/bootstrap must be checked by an authorized administrator. Vercel API/web status failures point to a build-rate limit, not Python test failures.
- **Stack integration risk:** #271 currently reports non-mergeable against #414 following governance changes. Recheck ancestry and conflicts before fixing the downstream branch.
