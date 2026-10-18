# Goal

BoardGamesWithQuests is a configurable board-game project that combines chess, English draughts, game-state management and quests. The first product milestone is a **complete local Python/Tkinter application**; the later server/database/web/native-client architecture is a separate milestone.

## Success criteria

- Verify chess and draughts gameplay, clocks, quests, settings, notation and the full Tkinter user flow through observable behavior.
- Maintain one authoritative game engine, coherent controller/view ownership and no hosted-service dependency in desktop v1.
- Build native Windows x64, macOS ARM64/x64 and Linux x64 packages; verify real installed startup, bundled resources, gameplay and checksums.
- Release **v1.0.0** through approved `develop → main` promotion and DarkFactory PrideVer, with verified provider branch protections and all required assets.
- Keep each PR's requirements, architecture, documentation, tests and diagrams consistent with code actually in that branch.

**Working documents:** [Plan](PLAN.md) · [TODO](TODO.md) · [Scratchpad](SCRATCHPAD.md). Approved current requirements and accepted architecture are authored in `requests/` and `decisions/`. Proposed future API/database contracts remain in GitHub issues.
