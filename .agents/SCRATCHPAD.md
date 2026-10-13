# Current integration verification

**Source of truth:** [PLAN](notes/PLAN.md) · [PRD](notes/PRD.md) ·
[JSON contract](notes/json_contract.md) ·
[Integration PR #271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271) ·
[Completion issue #129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129) ·
[Final behavior gate #239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239).

## G0 — complete

- Single draft integration PR, no maintainer approval or merge into main.
- Both recovery branches retained in integration Git ancestry and deleted as refs.
- All 22 inline review threads addressed and resolved.
- Global GitHub Project #17 and local Project #14 links verified.
- Actions run `38397182126` audited 216 project items, reconciled 81 statuses,
  and verified every result on a subsequent read.
- DarkFactory v0.289.2 pinned on the integration/managed configuration paths.

## G1 — implemented; final checks required

- JSON version 2 strictly validates declared board/pieces, quests, rule hooks,
  bounded ASTs, typed references, capture policies and clock constraints.
- Pure evaluators plan effects without mutating the authoritative game.
  Generic capture geometry supports short/flying kings, multi-hops, backward
  captures, deferred captured-piece obstruction and maximum capture checks.
  Generic snapshot/position/rights/castling/transient-target/promotion and
  outcome precedence primitives are exercised through
  `scripts/probe_g1_semantics.py`. The separate negative-input/AST probe is
  `scripts/probe_json_contract.py`.
- These are **G1 expressiveness probes, not G3 complete legal game rules**.
  Chess, English draughts and international draughts all remain
  `playable=false`.
- Public Vercel Hobby frontend and FastAPI host are READY. Actions
  `hosted-bootstrap` passed unauthenticated live HTTP probes against
  `https://boardgameswithquests-api.vercel.app/health`,
  `https://boardgameswithquests-api.vercel.app/games` and
  `https://boardgameswithquests-web.vercel.app/`.
- Reused the existing Supabase `reactgame` project, reference
  `wdthdcdoqdtywngwvddk`, at the user's direction; resumed it from
  INACTIVE to ACTIVE_HEALTHY. No new paid project was created.
- Deployed isolated **private** `bgwq` schema migrations
  `20261013145509_private_game_persistence` and
  `20261013151643_immutable_game_snapshot`. No unrelated tables altered.
  Both tables have RLS enabled; anonymous/authenticated roles cannot access
  the schema, tables or private revision function.
- Actual Supabase SQL transaction probes succeeded: approved participant
  advances revision + inserts exactly one event; outsider and stale submissions
  are rejected without state changes; config/participant identity mutation
  is forbidden. Both temporary test rows were removed; DB contains zero
  `bgwq.games` entries after probes.
- The Supabase security advisor reports pre-existing exposed `public`
  tables from the reused project. They were **not altered**; G4 must audit
  their exposure before publishing the project's client key. Private
  `bgwq` RLS-with-no-policy notices are expected for server-only tables.
- Shared-school-IP anonymous sign-in quota (normally 30/hour/IP, configurable)
  remains a real capacity risk. G4 enables guest login; G7 must verify
  classroom-size anonymous sign-in capacity before public presentation.
- Await the final green aggregate quality check on the current PR head to
  certify the G1 code checkpoint.

## Next: G2/G3

G2 must implement generic state reconstruction, trusted authenticated move
authorization, full effect execution, clocks, quests, outcome adjudication and
an atomic game/domain transaction invoking the already-probed SQL boundary.
G3 must provide complete FIDE and both draughts rulebooks using only game JSON
plus trusted generic primitives and correct game-owned exporters.
G4 adds Supabase registered/anonymous Auth, secure backend connection,
Realtime and the React two-participant client. G6/G7 remain mandatory.
No merge or claim of playable class deployment before G7 and maintainer approval.
