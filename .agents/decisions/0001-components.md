---
status: accepted
---
# Authoritative local game domain

## State and transitions

`model.game.manager.GameManager` is the sole authoritative game transition owner. A session pins one validated `GameDefinition` and participant identities; each accepted action advances exactly one revision and records an event. Candidates are evaluated against isolated mutable projections and published as immutable JSON state only after all legal, rule, clock and effect checks pass. Duplicate identical action IDs return their original event, conflicting reuse is rejected, and `from_snapshot` reconstructs and validates state by event replay.

`model.game.session.DesktopSession` is the durable local application boundary. It creates and resets games, exposes detached state and board projections, enumerates legal actions, submits actor-bound moves, polls clock expiry and recovers from snapshots. It depends only on the Python domain and local time/IDs; no hosted runtime is involved.

## Board and declarative rules

`Board` is generic rectangular storage for `Piece` values built from the immutable game JSON definition. `Move` represents an immutable source, complete landing chain and optional promotion; `MoveValidator` provides read-only geometric move/attack vectors. `CaptureEnumerator` calculates bounded capture chains. `RuleProgram` and `ConditionEvaluator` evaluate validated game-owned hook conditions using `BoardQueries` and `SnapshotQueries`; only whitelisted effects are committed. `resolve_outcome` rejects contradictory equal-priority terminal proposals.

## Clock and quest state

The authoritative snapshot includes participant clocks, accepted event history, capture lists, per-participant quest progress and earned quest scores. Quest conditions run only after accepted moves; speculative legal-action previews cannot award rewards. Active time is charged at authoritative action submission. The UI draws detached current values and polls timeout from the session.

## Game definitions

`src/games/chess/config.json` and `src/games/checkers/config.json` define piece capabilities, initial placement, hooks and quests; their `playable` flag is currently false. English-draughts kings declare short-range movement, unlike flying variants.
