---
status: published
---
# Current source and repository layout

| Path | Current responsibility |
| --- | --- |
| `src/chesswithquests/` | Application entry, installation diagnostic and Tkinter startup |
| `src/controller/` | Square input, selection, game lifecycle and window state |
| `src/model/game/` | Python-constructed game configs, board, validator, manager, rules, clocks and quests |
| `src/model/misc/`, `src/model/pieces/`, `src/model/users/` | Game export/notation, shared pieces and user state |
| `src/games/chess/`, `src/games/checkers/` | Python variant-specific boards, pieces, rules and clocks |
| `src/view/` | Tkinter app, board/player/quest widgets, settings and Python source editor |
| `.agents/notes/`, `requests/`, `decisions/`, `rules/` | Authored sources for generated README, PRD, ARCHITECTURE and AGENTS |
| `.agents/{GOAL,PLAN,TODO,SCRATCHPAD}.md` | Outcomes, phase plan, open queue and temporary evidence |
| `.agents/architecture/diagrams/`, `.agents/reference/` | Source-generated Mermaid and reference assets |
| `.github/tests/`, `scripts/`, `workflows/` | CI, generated docs, test fixtures, packaging and guarded release |

The old `packages/engine/` runtime does not exist in this PR's working tree. The hosted server/client/native layers are deferred to #422. The root README and CONTRIBUTING are symlinks to generated documentation.
