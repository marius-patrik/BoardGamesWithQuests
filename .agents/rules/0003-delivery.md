---
status: active
---
# Planning and change delivery

- Translate desired functionality into an issue with explicit acceptance criteria and a bounded plan before implementing. Do not place future API/SQL/DSL/design contracts in repository documents. Keep `.agents/PLAN.md` and `.agents/TODO.md` as concise links to live issues and actual progress, not competing product specifications.
- Prefer small, cohesive, independently verifiable changes. Delegate independent work only when boundaries and integration contracts are clear.
- Work from a focused issue-bound bot-authored branch targeting its reviewed dependency. The existing #331 → #343 → #271 PR stack targets the current `main` lineage, requiring explicit maintainer review and approval for every merge. Issue #404 records a separate, **unexecuted** branch migration proposal; do not change the live default branch or assume `develop` exists.
- Preserve human approval gates; never bypass a review or required check merely to unblock a merge.
- Describe actual changes, verification and remaining gaps precisely in the pull request; update the PRD, architecture and operational governance sources to match the implementation in this very PR. Keep unrelated discoveries visible as separate tracked work.
- Use focused conventional commits such as `feat(ui): add navigation` or `fix(core): handle cancellation`.

### BoardGamesWithQuests: Change Granularity and Conventional Commits
Use focused, descriptive Conventional Commits in the form
`<type>(scope): description`. Keep each change coherent and reviewable rather
than manufacturing a commit for every class or bundling unrelated behavior.

### BoardGamesWithQuests: Branches and Pull Requests
Use focused, descriptive, lowercase topic branches based on the intended
target branch. Never push directly to protected `main`. Open Draft PRs
through the repository's authorized bot-authored PR workflow so the maintainer
can provide an independent native approval. Each PR binds its actual tracked
issue, contains one coherent responsibility and identifies remaining
dependencies rather than bundling incomplete neighboring components.
Synchronize with the target branch and rerun applicable checks before merge.
Merges require explicit maintainer approval. After cutover, promotion from `develop` into `main` requires a **separate explicit request**; regular integration merges must never publish to the release branch.

### BoardGamesWithQuests: Issue and Project Tracking
Bind every pull request to an implementation issue. Keep issues and project
board statuses consistent with verified results; do not close unfinished
requirements or represent a blocked external acceptance as complete.
Preserve the repository's functioning issue and branch automation without
creating overlapping management workflows.

### BoardGamesWithQuests: Planning and Review
Record each work item's outcome, architectural interfaces, dependencies,
review criteria and verification evidence in its implementation issue.
Align plans and specifications whenever decisions change; replace superseded
instructions at their source. Conduct independent implementation, security
and artifact review as applicable. Do not claim conformance until the
behavior, documentation and approved criteria agree.

### BoardGamesWithQuests: Approval and Merge
The maintainer must explicitly approve the final reviewed commit before
merge. Passing CI is necessary but never sufficient for functional acceptance.
Do not activate unattended auto-merge or proxy approval as a substitute for
the maintainer's native review. Merged branches may be deleted after their
commits and linked issues have been reconciled.

### BoardGamesWithQuests: Request Authorization
Record material implementation requirements and accepted scope in a linked
issue. Preserve the user's meaning and acceptance criteria. Explicit user
authorization for an implementation does not require a duplicate approval
step. Escalate unresolved architectural decisions, credentials, unrelated
data deletion or new financial commitments before taking such actions.

### BoardGamesWithQuests: Commit and Area Taxonomy
Use Conventional Commit types `feat`, `fix`, `refactor`, `docs`,
`test`, `chore` and `ci`. Use descriptive scopes. Assign issue
areas by the actual affected responsibility: model, game, server, web,
desktop, CI or documentation. A label is not a substitute for a verified
capability or complete implementation.
