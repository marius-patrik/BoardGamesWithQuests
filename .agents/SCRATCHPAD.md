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
- Configure authenticated Supabase integration and game-server authorization.
- Perform real two-participant, race/retry and reconnect acceptance, desktop
  tests and classroom guest-capacity rehearsal.
- Keep PR #271 draft until all gates pass and the maintainer approves.

## Engine dependencies

- Add bounded configured `available_moves` offers and prospective-state safety
  evaluation so castling, en passant and royal safety pass the same transition
  boundary as ordinary moves. Bind optional promotion choices to legal offers;
  reject unoffered kinds and implement complete crowning policies.
- Provide declarative temporary-target initialization, updates and expiry,
  configured starting rights and recoverable per-rule state. Align JSON schema,
  interpreter, session snapshot and shipped definitions in each chunk.
- Define configurable halfmove-reset and position-identity policies. Exact
  chess repetition must depend on available rights and legally meaningful
  en-passant eligibility; irrelevant movement flags must not split equivalent
  positions. Test repetition through actual accepted sequences and replay.
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

- Connect domain snapshots/events to authenticated Supabase-backed atomic
  commits. Verify real JWT identities, participant isolation, stale/duplicate
  requests, concurrent server instances, rollback and process reconstruction.
- Implement registered/guest identity flows, owned variants, game creation and
  joining with exactly two participants; provide generated API/frontend types.
- Build authoritative React gameplay and schema-driven settings, then exercise
  real two-browser interaction, Realtime loss/reordering/reconnect and complete
  games. Verify the same hosted frontend in the Tauri wrapper.
- Verify public API/web deployment revision compatibility and protected-service
  configuration. Run provider integration and classroom shared-IP capacity gates;
  a build or headless session cannot satisfy public delivery.

## External constraints

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
