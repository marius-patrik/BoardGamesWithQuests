## Scope and contract

<!-- Describe only behavior actually present on this PR's final commit. Proposed API/DB/DSL/client/game contracts and intended target trees belong in the linked issue, not as implemented repository facts. -->

## Linked issue

<!-- Bind through Closes #NUMBER / Fixes #NUMBER / Resolves #NUMBER; a bare link does not satisfy the native issue-binding check. -->
Closes #

## Changes and dependencies

<!-- Describe permanent implementation surfaces; list affected packages, schemas, docs, diagrams, CI and deployments. -->
<!-- State unresolved dependencies and work that remains outside this PR. -->

## External behavior verification

<!-- Supply commands/links and observed input -> action -> outcome evidence. -->

- [ ] Supported user/consumer/provider path exercised; observed output or durable effect verified
- [ ] Adversarial and boundary cases covered, including authorization and concurrent state changes where applicable
- [ ] Regressions fail on the defective behavior and pass after the correction
- [ ] Provider, database, browser and packaged application gates run when required
- [ ] Unavailable mandatory external gates declared **BLOCKED**, never replaced by mocked passes
- [ ] Typecheck, build, format, documentation and package validation pass where applicable

## Governance source verification

- [ ] **Actual state:** every assertion in README, PRD, ARCHITECTURE, AGENTS, diagrams, examples and deployment notes matches this PR's **actual committed source and observed behavior**; prospective contracts remain only in GitHub issues
- [ ] **Same-PR reconciliation:** all affected authored governance records, generated projections, source-derived diagrams, tests, CI, examples and documentation are synchronized in **this PR**, not deferred
- [ ] **Issue-only future design:** no proposed but unimplemented API/DTOs, database tables, DSL/operator registry, game rules or client mockups are committed as the actual contract

- [ ] Updated any affected `.agents/{notes,requests,decisions,rules}/` source record and regenerated README, PRD, ARCHITECTURE and AGENTS in one diff
- [ ] `python3 .github/scripts/generate_documents.py --check` passes, including symlinks, unchanged DarkFactory metadata and `.github/tests/` ownership
- [ ] The base branch and review policy match the **actual GitHub configuration**; no branch cutover or release promotion is implied by this PR.

## Artifact alignment

- [ ] APIs, implementations, configuration, schemas, migrations, game JSON, tests, documentation and diagrams agree
- [ ] Links, example commands, issue criteria, deployment and release metadata updated where affected
- [ ] No unused parallel authority, fake readiness, disposable scaffold or historical commentary introduced
- [ ] No credentials or privileged operations exposed to public clients
- [ ] Independent reviewer has checked implementation, security and actual acceptance evidence
- [ ] `.darkfactory/` and release/branch controls are unchanged unless separately authorized and verified
- [ ] Draft remains unmerged pending explicit maintainer approval

## Independent reviewer verification

- [ ] Reviewer inspected the final commit, actual diff and provider/user behavior, not just issue acceptance text or green structural checks
- [ ] Reviewer independently confirmed source/documentation accuracy, link and workflow behavior, and flagged any unverified external acceptance **BLOCKED**
- [ ] Explicit maintainer approval is still required; CI, bot reviews and a passing docs preview do not approve a merge or prove Pages publication

## Acceptance status

<!-- Distinguish VERIFIED, BLOCKED and OUT OF SCOPE. Never claim product readiness based only on green build checks. -->
