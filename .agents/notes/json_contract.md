# Declarative game behavior contract

The current parser accepts schema version 2 with finite `rules` and `quests`
arrays. Expressions are typed objects, never Python/JavaScript expressions.
The five hooks are `permits_move`, `available_moves`, `outcome`,
`on_move_made` and `status`. A rule has
`{id, hook, when, effects}`. A quest has
`{id, description, when, reward}`. Each condition is a typed
`true/false`, `all/any/not`, `test`, or `compare` node.
Queries and effects are restricted to the explicit whitelists in
`packages/engine/model/game/schema.py`.

**Contract stage:** validation is implemented; interpreting conditions,
generating special moves, mutating state through effects and proving three
game-rule expressiveness are **not** implemented. The shipped configurations
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
