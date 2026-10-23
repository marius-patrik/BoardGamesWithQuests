# TODO — v1.0.0 completion queue

**Owner:** [v1 issue #430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430). Read [PLAN](PLAN.md) for ordered acceptance. **v2 architecture:** [issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348), deferred after v1 release. Do not start a second engine or GUI.

- [ ] **P0 correctness:** Fix actual English-draughts timeout/no-legal-moves precedence on current #271 head. Verify terminal conflicts, repeated actions, atomic failures, replay and exact-head Python matrix.
- [ ] **P0 inventory:** Read-only module-by-module cleanliness audit (dead/duplicate/misowned/historical code and misleading types), and historical Chess/draughts/quest/clock/UI parity classification.
- [ ] **P0 test redesign:** Classify every `.github/tests/` test by real observable acceptance and independent oracle; design replacement application-boundary, real Tkinter, real native-binary suites. Replace ineffective tests as equivalent proven coverage lands, not as a mass deletion.
- [ ] **P1 quality:** Apply focused readability/architecture cleanup; eliminate obsolete paths, unnecessary indirection and redundant state/logic without changing working gameplay. Independently review refactor diffs.
- [ ] **P1 games:** Independently verify complete Chess/English-draughts games and rules, clocks/quests/outcomes, replay/budget/security; mark definitions playable only after complete proof.
- [ ] **P1 GUI:** Visually inspect and polish the **existing Tkinter application** (layout, typography, board, player/quest/history, legal selection, dialogs, resize/DPI/focus/accessibility, feedback and shutdown) using actual screenshots and interactions.
- [ ] **P1 native QA:** Exercise actual extracted Windows x64/macOS ARM64/macOS x64/Linux x64 frozen GUI and gameplay, preferences/restart/shutdown, bundled JSON/version/provenance and checksums. `--check` or five-second process survival alone is not acceptance.
- [ ] **P0 release audit:** Run final exact-SHA CI and mandatory graphical/native gates; reconcile review feedback; regenerate truthful current-state docs and diagrams; obtain independent approval on #271.
- [ ] **Maintainer gate:** Merge approved #271 into `develop`, separately authorize `develop → main`, publish via PrideVer and verify all four **public, downloadable, playable** v1.0.0 artifacts.

**Deferred:** v2 FastAPI/Supabase/React/Tauri/multiplayer #348/#422. **Out of scope:** expanded exports, GUI/engine rebuild, speculative compatibility and new variants.
