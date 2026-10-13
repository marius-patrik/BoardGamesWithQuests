# Current Integration Status

**Authoritative work:** [PLAN](notes/PLAN.md) · [PRD](notes/PRD.md) ·
[Object model](notes/object_model.md) · [Implementation PR](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271) ·
[Plan issue](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129) ·
[Final behavior suite](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239).

## Verified state

- One draft integration PR targets main; no maintainer approval to merge.
- Source ancestry includes the recovery chain, while active sources use JSON-owned
  game definitions. Git ancestry is not proof that its code was integrated.
- Python board geometry and config discovery exist. Legal rules, quests, result
  evaluation, game exports, authentication, transactions and the GUI are incomplete.
- UI, API and desktop package skeletons are tracked independently from real operation.
- Permanent gameplay test coverage and public deployment are absent; green
  compilation/docs checks do not certify gameplay.
- PR #271 membership on Global project #17 is confirmed by an authenticated
  GraphQL read after mutation. All 211 items on project #14 were audited:
  24 closed issues still show In Progress, 15 show ToDo, and 21 closed PRs
  show In Progress. Reconciliation is scripted, but last write run could not
  execute because the owner-scoped token exhausted its GitHub API rate limit.
  The seven closed-not-planned issues incorrectly labeled Done are corrected.
  G0 therefore remains **partial** until a successful project field write/read audit.
- DarkFactory v0.289.2 is pinned in CI and both live and dedicated configuration
  branches; native tool config generation is tracked upstream in DF #2149.
- CI builds the actual static Rsbuild web bundle and imports the FastAPI ASGI
  health route. Authentication, real moves and public hosting remain absent.
- G1 includes a bounded condition evaluator and deterministic non-mutating
  hook effect planner; these do not yet prove chess or draughts legality.

## Execution gate

Complete bounded JSON schema and representative three-game expressiveness probes;
verify FastAPI/Vercel packaging, Supabase transaction and anonymous sign-in
classroom quota feasibility. Then implement domain rules, game conformance, secure
server/UI, desktop packaging and end-to-end tests. Do not merge before explicit
maintainer approval and the complete release gate.
