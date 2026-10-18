# Plan — BoardGamesWithQuests

**Target:** standalone Python/Tkinter `v1.0.0` · **Integration:** `develop` · **Release:** `main`

The repository foundation and release/provider setup on #414 are **handed off to the authorized local agent**. Their remaining work and acceptance are recorded in that agent's execution instructions, **not duplicated in this plan**. Do not treat #414 as merged or provider policies as enforced until the agent supplies verifiable evidence and the maintainer approves.

## Execution order

| Phase | Owner | Remaining outcome | Status |
| --- | --- | --- | --- |
| **1 — Desktop** | **#271** | Complete and verify the Python/Tkinter application, mandatory GUI acceptance and native packaged distributions | Pending #414 approval/integration |
| **2 — Release** | Promotion PR | Approve `develop → main` and automatically publish verified `v1.0.0` | Pending desktop acceptance |
| **3 — Migration** | **#422** | Complete and verify FastAPI, Supabase, React, Tauri and multiplayer | Deferred until v1.0.0 |

**Stack:** `develop → #414 → #271 → #422`.

## Completion criteria

- [ ] #271 is mergeable after #414 integration; chess and draughts are playable through real Tkinter GUI acceptance, applicable reviews are addressed, and four native distributions are tested.
- [ ] #271 is reviewed, approved and merged into `develop`.
- [ ] Approved same-repository `develop → main` promotion automatically publishes `v1.0.0` through PrideVer for the exact commit with four verified distributions and checksums.
- [ ] #422 remains excluded until the desktop release succeeds and is verified.

## Phase 1 — Python/Tkinter application (#271)

- [ ] Synchronize #271 with the verified #414 result and resolve its current non-mergeable state; review the complete desktop diff, game/controller/view state, imports, configuration ownership and runtime resources.
- [ ] Complete and verify chess and English-draughts rules and outcomes, clocks, quests, settings, notation/exports, persistence, error recovery, new games, and actual Tkinter interactions.
- [ ] Correct ineffective tests and require actual/virtual-display GUI acceptance without silent skips; verify the Python 3.10–3.13 quality matrix.
- [ ] Execute the native desktop packaging workflow defined on #414 against the finished `src/` app. Prove Windows x64, macOS ARM64/x64 and Linux x64 standalone startup, gameplay, resources, persistence, version and SHA256 artifacts; ensure failures block publishing.
- [ ] Reconcile outstanding #271 reviews and applicable historical #405 feedback. Update approved requests, accepted architecture, notes, diagrams, tests and generated docs in the same PR. Complete independent final review and seek maintainer approval.

## Phase 2 — v1.0.0 integration and release

- [ ] Merge approved #271 into `develop`; verify actual integrated GUI, tests and platform distributions.
- [ ] Confirm the delegated #414 handoff established the live `main` protections and trusted workflows before opening release promotion.
- [ ] Review and approve a same-repository `develop → main` PR with the exact intended SHA.
- [ ] Run the guarded PrideVer and native platform matrix after promotion; publish only the complete `v1.0.0` release.
- [ ] Independently verify public tag, source commit, all four downloads and their checksums.

## Phase 3 — Architectural migration (#422, after v1.0.0)

- [ ] Refresh #422 against the released desktop baseline and reconcile its owning implementation issues; fix actual Rust/Tauri Linux GLib CI failures.
- [ ] Complete FastAPI, Supabase authentication/database, React gameplay, Tauri, multiplayer, provider/deployment verification and applicable reviews; request maintainer approval before merging.

**Document ownership:** [GOAL](GOAL.md) contains outcomes, [TODO](TODO.md) the current queue, and [SCRATCHPAD](SCRATCHPAD.md) temporary evidence. The PRD and architecture describe actual code, not proposed future contracts. The delegated Phase 0 task has no competing tracked roadmap.
