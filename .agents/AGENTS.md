# Repository Development Guidelines & Agent Rules

### 1. Externally Observable Verification
Tests must exercise supported user, consumer or provider interfaces and assert
meaningful outcomes. Testing isolated implementation details, internal class
methods, mocked calls, imports, syntax or intentional unavailability is not
acceptable behavior evidence. A black-box test may run locally: the contract
crossed, rather than the test machine, determines whether the test is valid.

Cover successful operations, malformed and hostile inputs, authorization,
identity isolation, boundary conditions, concurrency, retries, idempotency,
failure rollback and recovery after reload or process restart where applicable.
Each fix needs a regression reproducing its observable defect. Provider,
database, browser and deployment acceptance requires the actual service;
unavailable mandatory gates are BLOCKED, never silently skipped or passed
using mocks. Compilation and documentation checks never certify gameplay.
Tests must be repeatable, isolated and capable of failing on broken behavior.

### 2. Generated Documentation and References
Documentation and navigation are generated from tracked repository source,
typed Google-style docstrings and the supported build tooling. Generated
documentation output is never edited as its own authority. Strict documentation
builds and source-derived architecture diagrams must succeed; supplied
reference diagrams are immutable input assets, not mandatory duplicate runtime
classes. Every affected link, example and diagram must remain correct.

### 3. Atomic Artifact Alignment
Each change updates **every affected artifact** together: behavior, public
interfaces, schemas, migrations, game JSON, tests and fixtures, contracts,
decisions, diagrams, generated documentation, examples, CI, deployments,
release metadata and issue/PR acceptance criteria. Delete contradictory
references and unused duplicate implementations; never defer required
synchronization to an unspecified cleanup.

GitHub issues own desired requirements and prospective implementation contracts;
repository documentation describes actual source, configured controls, and independently
observed behavior only. Each PR updates its own affected governance and tests. No plan, diagram, mock, passing build or hosted placeholder establishes
operational functionality.

### 4. Language Consistency
English is canonical for all code, method names, variables, comments, docstrings, commit messages and documentation. Existing compatibility interfaces must be preserved or changed through tested implementation. No proposed aliases or naming conventions are treated as implemented contracts.

### 5. Change Granularity and Conventional Commits
Use focused, descriptive Conventional Commits in the form
`<type>(scope): description`. Keep each change coherent and reviewable rather
than manufacturing a commit for every class or bundling unrelated behavior.

### 6. Verification and CI
Run the genuine applicable behavior suite and independent adversarial review
with every production change. Required status checks must accurately reflect
their actual coverage. Typechecking, formatting, compilation, documentation
and packaging are valid engineering checks but never substitute for a missing
external behavior or security acceptance gate. Do not weaken required checks
to manufacture a green PR.

### 7. Branches and Pull Requests
Use focused, descriptive, lowercase topic branches based on the intended
target branch. Never push directly to protected `main`. Open Draft PRs
through the repository's authorized bot-authored PR workflow so the maintainer
can provide an independent native approval. Each PR binds its actual tracked
issue, contains one coherent responsibility and identifies remaining
dependencies rather than bundling incomplete neighboring components.
Synchronize with the target branch and rerun applicable checks before merge.
No merge or production promotion occurs without explicit maintainer approval.

### 8. Format and Source Quality
Use the repository's configured formatters and typecheckers. Format
changes must remain scoped to relevant files and must not replace real
behavior testing.

### 9. Issue and Project Tracking
Bind every pull request to an implementation issue. Keep issues and project
board statuses consistent with verified results; do not close unfinished
requirements or represent a blocked external acceptance as complete.
Preserve the repository's functioning issue and branch automation without
creating overlapping management workflows.

### 10. Planning and Review
Record each work item's outcome, architectural interfaces, dependencies,
review criteria and verification evidence in its implementation issue.
Align plans and specifications whenever decisions change; replace superseded
instructions at their source. Conduct independent implementation, security
and artifact review as applicable. Do not claim conformance until the
behavior, documentation and approved criteria agree.

### 11. Approval and Merge
The maintainer must explicitly approve the final reviewed commit before
merge. Passing CI is necessary but never sufficient for functional acceptance.
Do not activate unattended auto-merge or proxy approval as a substitute for
the maintainer's native review. Merged branches may be deleted after their
commits and linked issues have been reconciled.

### 12. Request Authorization
Record material implementation requirements and accepted scope in a linked
issue. Preserve the user's meaning and acceptance criteria. Explicit user
authorization for an implementation does not require a duplicate approval
step. Escalate unresolved architectural decisions, credentials, unrelated
data deletion or new financial commitments before taking such actions.

### 13. DarkFactory Integration
Use the installed DarkFactory-managed pipeline and `repo.dfconfig` as the
single authoritative DarkFactory configuration. Keep supported native
manifests when build tools require them. Do not maintain parallel workflow
implementations, duplicate credentials configuration or copies of shared
harness logic. Pin verified external workflow and action dependencies.
Do not delete native manifests until their generation/replacement passes
the actual consumer build and deployment checks.

### 14. Commit and Area Taxonomy
Use Conventional Commit types `feat`, `fix`, `refactor`, `docs`,
`test`, `chore` and `ci`. Use descriptive scopes. Assign issue
areas by the actual affected responsibility: model, game, server, web,
desktop, CI or documentation. A label is not a substitute for a verified
capability or complete implementation.

### 15. Timeless Repository Artifacts
Tracked files contain only authoritative requirements, design decisions,
working implementation descriptions, reproducible source inputs and
actionable unfinished work. Do not keep implementation histories, dated
progress narratives, superseded instructions, transitional comparisons,
obsolete files or phase-relative labels that do not express a stable
functional contract. Replace material at its source instead
of appending chronicles. Git and issue history retain provenance; source
citations and ordered SQL migrations may carry required date identifiers.

### 16. No Disposable Production Implementations
Do not add or retain placeholder UIs, bootstrap-only endpoints, fake
health/readiness states, intermediate servers, throwaway CLIs or tests that
merely certify an unavailable feature. Only permanent supported behavior
belongs in a mergeable production path. Record unmet requirements as
blocked without manufacturing substitutes.

Use Python namespace packages for directories that need no executable
initialization; verify built distributions, import discovery and packaged
resource loading before removing initializers.

### 17. Secrets and External Operations
Never expose privileged service tokens to public consumers. Server
authorization must verify the authenticated actor, not client-provided
identity claims. Where an external provider is unavailable, a destructive
operation is blocked or a paid resource is required, report the precise
limitation. Do not claim unexecuted verification or side effects succeeded.
