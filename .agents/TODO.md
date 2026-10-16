# Open Engineering Decisions and Investigations

## Timeout and position legality

- Investigate whether `GameManager._terminal_action()` computes `legal_move_count` under an expired clock and therefore reports zero executable actions even when geometric/game-rule-legal moves exist.
- Decide and document distinct semantics for **position legality** versus **time-dependent action eligibility** in the JSON query contract.
- Reproduce with an authoritative user-action scenario: identical position immediately before and at flag fall, with outcome arbitration requiring legal-move facts; assert durable result and unchanged rejected states.
- Apply a correction only after the behavior is reproduced and its rule semantics agreed.

## Testing strategy — decision on hold

- Decide whether any narrowly scoped domain/contract test is permitted in addition to externally observable API/provider/browser tests. Until decided, **local-only implementation tests must not count toward acceptance**.
- Specify exactly which public boundaries are authoritative for JSON parsing, rule interpretation, multiplayer state, export formats and desktop interaction.
- Replace isolated `GameManager`, `UserManager`, `Timer`, and `QuestManager` tests with user/provider-observable scenarios where an interface exists; mark missing externally testable functionality BLOCKED rather than manufacturing a local green test.
- Cover adverse inputs, authorization, game invariants, race conditions, retries, persistent state after restart and simultaneous player observation.
