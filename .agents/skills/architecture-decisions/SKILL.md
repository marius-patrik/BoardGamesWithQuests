---
name: architecture-decisions
description: Separate pending design choices in issues from accepted architecture implemented in code.
---
# Architecture Decisions

## When to use

When an implementation changes structure, module authority, provider boundaries or irreversible technology decisions.

## Procedure

1. Inspect committed implementation and current issue decisions.
2. Review **proposed** alternatives in the owning GitHub issue, not a prematurely accepted in-repo design record.
3. Once the code change implements the accepted choice, write or update one `.agents/decisions/<sequence>-<slug>.md` source record describing **what actually changed** and its consequences.
4. Remove or supersede contradictory source records in the same PR, and synchronize requests, rules, tests and source-derived diagrams.
5. Regenerate `.agents/ARCHITECTURE.md` and verify the final commit. External behavior remains unverified until exercised.

## Evidence

Implemented code, reviewed decision source and regenerated actual-state architecture. No speculative contracts in generated architecture.
