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
- G0 complete: PR #271 is verified on Global #17 and local #14. Both recovery
  branches were absorbed and deleted. GitHub Actions run 38397182126 scanned
  all 216 current project #14 items, corrected 81 outdated statuses from
  GitHub's actual states, and verified the results by re-reading all items.
  The temporary reconciliation workflow was then removed.
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

## Hosting bootstrap verified

- Vercel Hobby project `boardgameswithquests-api` was created (ID
  `prj_7kdxZvwbxItXRjRTblmz2s0xFw3h`); deployment
  `dpl_2TmHrJJ2qNXT54cbum4BDtmrFqwU` from commit `c7a47fcc`
  is reported READY by Vercel.
- Vercel Hobby project `boardgameswithquests-web` was created (ID
  `prj_iWSGkCmiCeh1uliqVN06b5QWPAAx`); deployment
  `dpl_2Sy36YSuA7Yx91cPuMEny3nWrv1P` from the same commit
  is reported READY by Vercel.
- Both projects currently have Vercel Authentication protection enabled;
  external unauthenticated HTTP reachability and working API routes were not
  demonstrated. READY is a build/deploy result, **not proof of online gameplay**.
- Supabase has no BGwQ project yet. Existing unrelated projects were left
  untouched. New project creation requires choosing an organization and
  confirming provider costs. No database schema, Auth, or Realtime deployed.
