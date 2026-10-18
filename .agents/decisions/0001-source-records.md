---
status: accepted
---
# Actual-state governance

## Decision

Use a status-gated source-record system: published notes generate README; approved requests generate PRD; accepted decisions generate ARCHITECTURE; active rules generate AGENTS. The generated files are deterministic, committed and never edited separately.

Repository documents describe **only current tracked/observed capabilities**. Implementation designs, API shapes, data schemas, target diagrams and future rules belong only in GitHub issues, not in generated PRD or architectural records.

## Consequences

Every PR with an implementation or governance change updates the affected source records, regenerates all affected outputs, checks their exactness, and labels any unverified external behavior BLOCKED rather than IMPLEMENTED.
