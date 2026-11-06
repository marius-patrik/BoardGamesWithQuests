# BoardGamesWithQuests — v1.0.0 Action Queue

**Canonical issue:** #430 · **Code PR:** #495 (`v1 → develop`) · **Promotion PR:** #501 (`develop → main`) · **v2:** #348 / PR #496. See [PLAN.md](PLAN.md) for the exact 16-file allowlist, Mermaid reference/file-map diagrams, naming contracts and ordered roadmap.

## Phase 1 — Python Chess, UML alignment, dialog-free UI

- [ ] Produce the exact 16 production Python files: `main.py`; model `user, player, board, piece, move, validator, manager, game, condition, timer, quest, logger`; view `app, game, panel`. Czech primary class identifiers + English aliases where specified by UML; English elsewhere; English filenames.
- [ ] Implement Python-defined Chess only; complete FIDE legality and terminal/draw conditions. Define `Hra` / `Game`, `Condition` and Check, Checkmate, Stalemate, DeadPosition, Threefold/FivefoldRepetition, Fifty/SeventyFiveMoveRule and Timeout subclasses within `model/condition.py`. Preserve four existing sourced Chess regressions.
- [ ] Consolidate model and controller logic into the allowed modules. Retain `GameManager` as transition authority, `Hra` as state/lifecycle owner, `RevizorTahu` as single legal-move validator and `GameLogger` as one atomic per-game JSON log under writable app data `data/logs/`.
- [ ] Deliver a **dialog-free and modal-free** Tkinter UI with modern monochrome ttk. Compose app, Canvas game, and two player panels; provide inline promotion, draw, resignation, new game, resume, errors and pending adjudication.
- [ ] Relocate repository tests/scripts to root; migrate source/installed/native packaging to Python Chess; maintain focused FIDE/persistence/UI regressions and all four native build+smoke+checksum gates. Repair Docs workflow and consolidate failure reporting to #430.
- [ ] Address all 22 PR #495 review threads and the overall Python/UML review; obtain final maintainer review and required CI.

## Phase 2 — Publish and finish

- [ ] Approve and merge #495 → protected `develop`; verify live default-branch Docs deployment.
- [ ] Approve and merge existing #501 `develop → main`; publish PrideVer `v1.0.0` with four native archives and SHA256 sidecars.
- [ ] Provide native signing/install disclosures and links for maintainer-owned postrelease testing.
- [ ] Merge released `main` ancestry into `v2`, preserve PR #496, delete integrated `v1`, close #430. Final branches `main`, `develop`, `v2`; sole open issue #348.
