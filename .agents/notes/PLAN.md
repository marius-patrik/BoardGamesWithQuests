# Delivery Plan

**Product contract:** [PRD](PRD.md)  
**Architecture:** [object_model.md](object_model.md)  
**JSON rules:** [json_contract.md](json_contract.md)  
**Execution:** [SCRATCHPAD](../SCRATCHPAD.md)  
**Integration:** [PR #271](https://github.com/marius-patrik/BoardGamesWithQuests/pull/271)  
**Product issue:** [#129](https://github.com/marius-patrik/BoardGamesWithQuests/issues/129)  
**Release verification issue:** [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239)

## Outcome

Deliver a publicly accessible, secure, complete two-player online board-game
platform on the approved free-tier Vercel and Supabase architecture. Orthodox
chess, English draughts and international draughts must run through the same
JSON-driven Python engine with correct rules, quests, clocks and exports.
React/Rsbuild provides one web frontend, also used by a remote Tauri wrapper.
No rooms, leaderboards, game-specific executable rules or additional servers.
Do not merge the integration PR without maintainer approval.

## Execution architecture

Dynamically dispatch small, testable, dependency-aware work chunks through
specialized implementation agents. Freeze only the minimal interface required
to safely parallelize work. Independently review each chunk for correctness,
security and cross-package compatibility; fix findings and rerun acceptance
tests before marking it accepted. One orchestrator integrates into the shared
feature branch, owns the plan and maintains consistency across all artifacts.

**Testing is part of implementation, not an isolated final task.**
Every production change includes behavioral regression and edge-case tests,
actual public API/database integration where applicable, and negative security
cases. Complete the independent full-system suite in #239 using those
executable contracts, then perform adversarial and real-browser acceptance.
Use the behavioral standard in [AGENTS](../AGENTS.md).

## G2 — Authoritative generic gameplay

- Complete typed JSON evaluator and ordered effect executor with strict conflict
  resolution; no user-authored Python/JavaScript.
- One immutable, serializable game snapshot: board, active side, configured
  rules and rights, multi-hop move, clocks, history, outcome, quests and revision.
- Validate intent against legal candidates, active participant, turn, clock,
  configured hooks and active game state before any mutation.
- Commit one action, clock update, per-player quest progress and events through
  one atomic persistence boundary. Rejected/duplicate/stale/unauthorized actions
  leave the snapshot unchanged.
- Verify closed move/resign/claim_draw/timeout submissions, both event envelopes,
  configured starting side and selected position identity through replay.
- Implement participant-authorized agreed draw offer/acceptance. Verify both
  private SQL event envelopes through authenticated HTTP before remote exposure.
- Preserve game-neutral movement, ray attacks, captures, promotion, path
  enumeration, terminal detection, repetition and configured result precedence.
- Test every supported operation through external domain behavior, including
  malformed JSON, deliberate rule conflicts, simultaneous actions, restart
  recovery, clocks and per-participant isolation.

**Exit:** A headless game can run legal and illegal declarative scenarios,
serialize/reload state, and commit or reject independently reproducible moves
without branching on game names.

## G3 — Game definitions and exporters

- Complete the FIDE chess JSON definition: check/royal safety, legal moves,
  castling, en passant, promotion, repetition, draws, mate and stalemate.
- Complete English draughts JSON: 8×8, compulsory captures, full chains, short
  kings, promotion and terminal outcomes.
- Complete international draughts JSON: 10×10, backward captures, flying kings,
  maximum capture, captured-piece obstruction, crowning and results.
- Keep board and piece definitions data-only, with bounded capture policies.
- Implement game-owned notation writers, accurate PGN/SAN/FEN exports and
  durable transcripts without a format branch in the generic engine.
- Run official/rules-reference examples, adversarial cases, expected outputs
  and randomized legal/illegal sequences through the full engine.

**Exit:** Every shipped game executes complete sessions with accurate,
independently reviewed results through the identical rule executor.

## G4 — Online multiplayer and React

- Implement authenticated FastAPI game/config/session APIs using Supabase Auth,
  including anonymous guests and registered accounts.
- Verify JWTs, participant membership, legal intent, turn and revision before
  server-only private PostgreSQL compare-and-swap commits.
- Keep every configuration snapshot immutable; protect all personal state with
  appropriate API authorization/RLS. No privileged key in public assets.
- Enforce two-participant create/join invitations, reconnect, durable history,
  synchronized clocks and event replay/reconciliation via Supabase Realtime.
- Implement responsive React UI with board, pieces, selection, moves,
  captures, clocks, quests, results, history and JSON-backed settings forms.
- Verify actual two-client, wrong-user, concurrent submissions, retry,
  failure/recovery and persisted gameplay flows.

**Exit:** Two distinct real identities can play and finish authorized
games across separate browsers, concurrent sessions and process restarts.

## G5 — Distribution and documentation

- Build Tauri 2 as a network wrapper of the same verified HTTPS React site,
  with minimal capabilities, secure navigation and auth callback behavior.
- Deploy Vercel API and frontend from compatible revisions using Actions.
- Align all README/package docs, PRD, contracts, decisions, migrations,
  configuration, generated architecture diagrams and release instructions.
- Enforce precise artifacts, timeless prose and atomic impact propagation.

**Exit:** Public web/API and desktop builds are reproducible and documented.

## G6 — Independent behavior verification

- Produce the requirements-to-scenarios matrix in #239 and run the actual
  behavior tests established alongside each product change.
- Test the full game rulebooks, rules/quests customization, auth/identity
  isolation, transactions, attacks, clocks, outcome tie resolution, exports,
  serverless restart, Realtime resynchronization and all UI interactions.
- Conduct separate code/design, adversarial security and integration review
  rounds. Close blocking defects with regression tests.

**Exit:** Independent behavioral and security verification passes with
evidence, not simulated readiness or syntax-only checks.

## G7 — Public rehearsal and approval

- Demonstrate real registered and anonymous participants, multiple concurrent
  games, a complete playthrough and refresh/reconnect on public endpoints.
- Verify free-tier guest sign-ins under shared-IP classroom load, provider
  quotas, clock accuracy, deploy compatibility and restart recovery.
- Check every artifact, workflow and GitHub issue/PR acceptance field against
  demonstrated behavior; request maintainer review and explicit merge approval.

**Exit:** Product requirements pass public acceptance and an independent
reviewer certifies the single PR ready for maintainer decision.

## Stop conditions and limitations

Unverified external actions remain blockers, not accepted substitutes.
No half-working fallback, silent test skip, branch proliferation, extra room
feature or privileged client credential. Iterate dependency-aware execution
and independent review until all exit conditions are met. Never merge without
the maintainer's explicit approval.
