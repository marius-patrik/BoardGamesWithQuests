# BoardGamesWithQuests

A JSON-driven two-player board-game platform for orthodox chess, English
draughts and international draughts. One game-neutral Python engine interprets
bounded JSON boards, piece capabilities, rules, quests, clocks and outcomes.
The delivery architecture places authoritative FastAPI play on Vercel Python
Functions, with Supabase authentication, database and Realtime. One
React/Rsbuild web app supplies the browser and remote Tauri 2 desktop UI.

Three shipped configurations are intentionally non-playable until complete
legal-rule integration passes the behavior suite. The public website and
read-only API catalog do not offer simulated gameplay.

## Source layout

- `packages/engine/` — generic geometry, conditions, effect planning and game state.
- `packages/chess/` — orthodox chess JSON definition and game-owned exports.
- `packages/english_draughts/` — 8×8 draughts JSON definition.
- `packages/international_checkers/` — 10×10 international draughts JSON definition.
- `packages/server/` — FastAPI ASGI boundary; `api/index.py` is the entry point.
- `packages/web/` — React/TypeScript/Rsbuild/Bun browser interface.
- `packages/desktop/` — Tauri remote-WebView wrapper.
- `supabase/migrations/` — reproducible private persistence and access migrations.
- `tests/` — behavioral definition, interpreter, capture, session and read-only HTTP tests.

## Interfaces

The public health and game-catalog API is hosted at
`https://boardgameswithquests-api.vercel.app`.
The browser application is hosted at
`https://boardgameswithquests-web.vercel.app`.

Gameplay and authentication require the remaining G2–G7 implementation;
all public catalog entries expose `playable=false`.

## Contract and contribution rules

- [Product requirements](.agents/notes/PRD.md)
- [Architecture decisions](.agents/notes/object_model.md)
- [JSON rule contract](.agents/notes/json_contract.md)
- [Delivery plan](.agents/notes/PLAN.md)
- [Engineering and behavior test requirements](.agents/AGENTS.md)
- [Reference diagram](.agents/notes/reference_diagram.md)

The game reference diagrams are supplied design inputs; source-derived
diagrams are generated independently. GPL-3.0-only governs the source.

## Behavioral verification

Install the Python package and development requirements, then run `pytest`.
The suite exercises validated JSON, immutable effect contracts, ordered-hop
intents, actor/turn/revision rejection, atomic domain rollback, exact retries,
clock transitions, participant-scoped quests and deterministic session replay.
Synthetic declarative scenarios exercise these contracts without claiming
complete shipped-game legality. HTTP tests cover health and the read-only
catalog; they do not certify multiplayer.

The executable `scripts/probe_g1_semantics.py` and
`scripts/probe_json_contract.py` supplement the permanent suite with primitive
expressiveness checks. Real Supabase transactions and authorization, public
multiplayer HTTP requests, two-browser gameplay, Realtime recovery, Tauri and
classroom shared-IP capacity each require their own integration gate. A passing
local suite does not certify those external requirements or a complete game.

The private SQL commit boundary accepts exact nine-field move events and exact
ten-field terminal events (`resign`, `claim_draw`, `timeout`) in version-1
snapshots. Terminal commits preserve position and rule/quest state, charge only
the running clock without increment, and atomically append one configured
result. Rule legality and outcome arbitration remain engine responsibilities.
Run the mandatory PostgreSQL suites with the integrated terminal engine:

```sh
PYTHONPATH=packages python -m pytest -q tests/test_private_transactions.py tests/test_private_transactions_adversarial.py tests/test_terminal_transactions.py
```

These tests require Docker access and fail explicitly when PostgreSQL cannot
start. They verify local private transactions, not hosted multiplayer acceptance.

## Source documentation

Install Graphviz and the Python package with its development requirements:

```sh
python -m pip install -e . -r requirements-dev.txt
mkdocs build --strict
```

MkDocs, Material and mkdocstrings generate every documentation page, homepage
and navigation entry from tracked Python package source and Google-style
docstrings. `python .github/scripts/build_docs.py` provides the same strict
build through an ephemeral source directory. No static documentation pages,
manual indices or documentation source directories are committed. Authoritative
specifications remain in `.agents/notes/` and are linked to the checked-out Git
revision rather than copied into the site. Architecture diagrams are generated
from source, and supplied reference figures remain available as required assets.

CI requires behavioral tests on Python 3.10–3.13, formatting, Rust quality
checks, web quality checks, production web compilation and strict documentation.
The aggregate quality gate rejects missing discovery, unsupported mandatory
commands and absent, skipped or failed execution evidence. GitHub Actions
deploys the documentation from reviewed `main` through the Pages workflow.
