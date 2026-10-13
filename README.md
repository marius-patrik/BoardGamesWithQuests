# BoardGamesWithQuests

BoardGamesWithQuests is a configurable two-player chess and draughts project built around a reusable, game-neutral Python engine. The approved application architecture uses declarative **JSON** for boards, pieces, rules, quests and clocks; FastAPI on Vercel Functions for authoritative moves; Supabase for authentication, durable state and Realtime; and one React web interface shared with a Tauri desktop wrapper.

The architecture described here is the **product target**, not a claim that the application is already playable. Actual implementation and verification status belongs in the [scratchpad](.agents/SCRATCHPAD.md).

## Package boundaries

```text
packages/
  engine/     Python domain model and declarative rule/quest interpreter
  chess/                 Orthodox chess JSON definition
  english_draughts/      WCDF English draughts JSON definition
  international_checkers/ International draughts JSON definition
  server/     FastAPI Python Functions, Supabase game transaction API
  web/        React + TypeScript + Rsbuild + Bun + shadcn/ui + Tailwind
  desktop/    Tauri wrapper loading the deployed web application
```

Game configuration is validated data, **never executable user-authored code**. The engine authorizes rules and turns; the server verifies users and commits durable game state. A game has exactly two participants. Supabase Auth supports registered users and guests. The public website is the primary application; desktop users access the same hosted interface.

## Project documentation

- [Completion plan](.agents/notes/PLAN.md)
- [Product requirements](.agents/notes/PRD.md)
- [Approved object-model deviations](.agents/notes/object_model.md)
- [Original reference diagram](.agents/notes/reference_diagram.md)
- [Chess rules baseline](.agents/notes/chess_rules.md)
- [Current progress and verification evidence](.agents/SCRATCHPAD.md)
- [Operational development guidelines](.agents/AGENTS.md)
- [DarkFactory automation architecture](.agents/notes/automation_architecture.md)
