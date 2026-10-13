# Orchestration Workspace

Use this file only for **unfulfilled executable work**, blockers with a
reproduction command, assigned agents and immediately actionable dependencies.
Do not append progress chronology, dated releases, narrative recaps, superseded
instructions or manually duplicated CI statuses.

**Authority:** [PRD](notes/PRD.md) · [PLAN](notes/PLAN.md) ·
[Rules](AGENTS.md) · [JSON contract](notes/json_contract.md) ·
[Delivery PR](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271).

## Execution

- Execute G2 through G7 through bounded, independently reviewed and tested
  chunks, with one orchestrator coordinating integration.
- Each code change updates its affected behavioral tests, schemas, artifact
  references, architecture decisions, generated diagrams and delivery checks.
- Verify complete game legality and all user-visible gameplay before setting
  any shipped definition's `playable` property to true.
- Configure authenticated Supabase integration and game-server authorization.
- Perform real two-participant, race/retry and reconnect acceptance, desktop
  tests and classroom guest-capacity rehearsal.
- Keep PR #271 draft until all gates pass and the maintainer approves.

## External constraints

- Supabase project `wdthdcdoqdtywngwvddk` holds the private `bgwq`
  persistence boundary. It also contains private protected account records;
  user data is not disposable as a side effect of repository cleanup.
- Supabase Auth leaked-password protection requires dashboard configuration.
- The shared-IP anonymous signup quota needs measured classroom capacity.
