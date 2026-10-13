# Declarative game behavior contract

The versioned parser accepts schema version 2 with finite `rules` and `quests`
arrays. Expressions are typed objects, never Python/JavaScript expressions.
The five hooks are `permits_move`, `available_moves`, `outcome`,
`on_move_made` and `status`. A rule has
`{id, hook, when, effects}`. A quest has
`{id, description, when, reward}`. Each condition is a typed
`true/false`, `all/any/not`, `test`, or `compare` node.
Queries and effects are restricted to the explicit whitelists in
`packages/engine/model/game/schema.py`.

**Contract stage:** bounded validation and pure condition interpretation of
trusted generic queries are implemented. The actual game-specific query
primitives, legal move generation, effects, outcomes and three-game behavioral
expressiveness are **not** yet implemented. The shipped configurations
therefore declare empty rules and `playable=false`.

G1 acceptance requires executable scenarios for chess (check, castling,
en passant, promotion and repetition), WCDF English draughts (compulsory
multi-capture, short kings and crowning), international draughts
(10×10, flying kings, backward capture, maximum capture count, crowning).
No query vocabulary is deemed sufficient merely because its name appears here.
The engine cannot infer legality from piece vectors alone.

Hosting feasibility: Vercel supports Python FastAPI ASGI functions with Python
3.12 and 3.13 (Python 3.14 is also available). API bundling must include the
monorepo engine and respect the 500 MB uncompressed limit. Supabase anonymous
sign-ins currently default to **30 requests per hour per IP**, a possible
classroom shared-IP blocker. Both are unverified with a live project.

## Provider feasibility boundary

Vercel's Python runtime supports the root `api/index.py` ASGI entry, reads the
root `pyproject.toml`, supports Python 3.12–3.14 and limits a Python function
to 500 MB uncompressed. The scoped React/Rsbuild production bundle now passes
CI; a real hosted API deployment has **not** been verified.

Supabase's published anonymous sign-in quota is **30 requests/hour per IP**
(with burst capacity up to 30); shared school Wi-Fi may exhaust it. Rate limits
are configurable, but acceptable classroom capacity must be tested on the
actual Free-plan project before claiming readiness. Provider projects and
database transactions/RLS have not been provisioned.

## Effect planning

`HookInterpreter` evaluates matching rules in source-JSON order and returns
a pure `HookEvaluation`. The result cannot modify the board or authorize moves:
effect conflict resolution and atomic application are G2 work. The G1 fixture is
`scripts/fixtures/g1_hooks.json`, not executable game-specific Python code.

## Live deployment gate

The first FastAPI and Rsbuild packages now have Vercel Hobby project IDs and
builds reported READY from the same `c7a47fcc` revision. Both deployments
are behind Vercel Authentication; public access, function responses and Supabase
connectivity remain unverified. Do not mark G1 complete based only on READY.
