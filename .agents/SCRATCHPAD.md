# Orchestration Workspace

Use this file only for **unfulfilled executable work**, blockers with a
reproduction command, assigned agents and immediately actionable dependencies.
Do not append progress chronology, dated releases, narrative recaps, replaced
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
- Complete genuine registered/guest Supabase identity verification and participant-scoped game-server authorization.
- Perform real two-participant, race/retry and reconnect acceptance, desktop
  tests and classroom guest-capacity rehearsal.
- Keep PR #271 draft until all gates pass and the maintainer approves.

## Engine dependencies

- Verify reconstruction performance under classroom load and implement verified
  checkpoints or efficient replay before exposing snapshot recovery publicly.
  Preserve accepted-history reconstruction, exact retries and corruption checks;
  retain per-action ceilings and a monotonic aggregate derived from supported
  event capacity. Test lengthy orthodox and draughts sessions against service
  execution limits without replacing denied hostile work with a larger action budget.

- Compose declarative shipped special-movement offers and role-safety conditions;
  verify full castling rights, attacked transit squares, en-passant eligibility,
  choice promotion and both capture-chain crowning policies against rule references.
- Derive rights/target lifecycle and quiet initial movements from configured
  pieces, previous actions and board dimensions. Verify relocated layouts and
  apply configuration edits through the identical interpreter and commit boundary.
- Complete rule-specific halfmove-reset and position-identity policies. Exact
  chess repetition must depend on available rights and legally meaningful
  en-passant eligibility; irrelevant movement flags must not split equivalent
  positions. Test repetition through actual accepted sequences and replay.
- Expose configured status hooks through read-only session/API views without
  permitting mutations or recursive legal enumeration.
- Adjudicate expired clocks with configured material/outcome conditions using
  a trusted timestamp and durable transition; rejected moves alone must not
  stand in for timeout completion. Cover restart, retries and clock boundaries.
- Extend quests with configured after-move/at-game-end evaluation timing and
  measurable active/target
  progress, completion and per-account reward persistence. Verify one completion
  across retries, terminal events, transaction rollback and reconstruction.
- Compose and independently verify all shipped rulebooks. Cover chess special
  moves/draw claims/material outcomes, English mandatory chains/crowning and
  international maximum capture/deferred blocking/crowning. Keep configurations
  non-playable until their complete behavioral gates pass.
- Extend durable action transcripts beyond move actions to supported resignation,
  claims and timeout transitions; preserve event/snapshot outcome agreement
  through reconstruction and the database commit boundary.
- Implement game-owned SAN/PGN/FEN writers using authoritative state and history.
  Verify actual exports, metadata, ambiguity, promotions and terminal notation.

## Delivery dependencies

- Implement the authenticated durable game adapter over the private pending,
  activation and domain transaction functions. Bind every actor to verified
  Supabase identity, recover creation/genesis data for retries and detect a
  reconstructed already-accepted event before attempting another commit.
  Return its accepted event and latest authoritative snapshot. Verify real
  HTTP participant isolation, stale/conflicting keys, concurrent server
  instances, rollback and restart recovery.
- Implement registered/guest identity flows, owned variants, game creation and
  joining with exactly two participants; provide generated API/frontend types.
- Build authoritative React gameplay and schema-driven settings, then exercise
  real two-browser interaction, Realtime loss/reordering/reconnect and complete
  games. Verify the same hosted frontend in the Tauri wrapper.
- Verify public API/web deployment revision compatibility and protected-service
  configuration. Run provider integration and classroom shared-IP capacity gates;
  a build or headless session cannot satisfy public delivery.

## External constraints

- Genuine registered/guest identity acceptance requires configured
  `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, registered and guest access tokens
  and their expected UUIDs. Run `PYTHONPATH=packages python -m server.auth
  --verify-provider`; missing credentials are an explicit blocked gate.
  HTTP tests with isolated network transport verify local failure/privacy
  behavior and cannot certify actual provider accounts or anonymous sign-ins.

- Supabase project `wdthdcdoqdtywngwvddk` holds the private `bgwq`
  persistence boundary. It also contains private protected account records;
  user data is not disposable as a side effect of repository cleanup.
- Verify Supabase Auth security settings and the free-tier availability of
  leaked-password protection and abuse controls. Any paid requirement needs
  explicit authorization; do not declare the security gate satisfied by omission.
- The shared-IP anonymous signup quota needs measured classroom capacity.
  Missing provider access or unavailable integration binaries leave the specific
  external gate blocked; continue independent work and retain reproducible
  verification commands without substituting mocks.
