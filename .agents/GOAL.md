# Goal

BoardGamesWithQuests first delivers a **complete, production-ready, downloadable and playable local Python/Tkinter v1.0.0** for Chess and English Draughts. Its existing GUI and substantially recovered authoritative JSON game engine are the implementation baseline: refine them rather than building replacements. The deferred multiplayer/server/database/React/Tauri platform is a **separate v2 milestone**.

## v1.0.0 success

- One generic JSON-configured engine and one desktop session authority; complete, rulebook-correct Chess and English Draughts, clocks, quests and local user preferences.
- Cohesive, readable, maintainable source with no duplicated implementation, dead or misleading transitional paths, or player-authored executable rule code.
- A polished **existing Tkinter interface**, verified through real interaction and visual inspection, with correct resizing, pointer-based gameplay, standard dialog controls, feedback, turns, board/game selection, quests, clocks and terminal states.
- A replacement acceptance strategy based on **independent references and supported observable player interfaces**, not private method assertions or mocks standing in for gameplay. Fail closed for mandatory display/platform evidence.
- Four genuinely usable frozen packages (Windows x64, macOS ARM64/x64, Linux x64), tested after extraction for actual GUI/gameplay, settings, restart, shutdown, bundled resources and artifact/checksum correctness.
- Independent approval of PR #271, separately authorized protected `develop → main` promotion, and verified public PrideVer **v1.0.0 download** for all four platforms.

Existing export behavior is factual where implemented, but **new/expanded export functionality is not a v1 development objective**. **Keyboard-controlled board navigation is explicitly deferred from v1** (issue #448 closed not planned). No claim of full keyboard-only gameplay; preserve normal ttk dialog focus and button controls. Avoid unrelated feature growth or rebuilding working components.

**Issues:** [v1.0.0 completion #430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430) · [v2 target design #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348) · [DF task-scoped dispatch #2694](https://github.com/marius-patrik/DarkFactory/issues/2694). The v2 design is issue-only until implemented and approved; repository PRD, diagrams and architecture describe **actual committed behavior**.

**Working records:** [Plan](PLAN.md) · [TODO](TODO.md) · [Scratchpad](SCRATCHPAD.md).
