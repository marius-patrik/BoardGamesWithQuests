## Scope and contract

<!-- Document only observable behavior implemented at this PR head. Proposed application contracts stay in issue #348 until implemented, not in current-state repository docs. -->

## Linked issue

<!-- Bind the scoped (possibly consolidated) work item with Closes/Fixes/Resolves #NUMBER: this is required by native issue-binding CI. Separately reference the unified master. NEVER use Closes #348 because the master must stay open until all work is verified. -->
Closes #<scoped-issue-number>
Refs #348

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

- [ ] **Actual state:** every claim in README, PRD, ARCHITECTURE, AGENTS, code-derived diagrams and release/deployment docs is supported by **this final commit**; unimplemented designs stay in issue #348
- [ ] **Same-PR reconciliation:** all affected authored governance records, generated projections, tests, examples, CI and documentation are updated **within this PR**, with no deferred clean-up
- [ ] **No premature contracts:** proposed endpoints, DTOs, data schemas, operator registries, game rules or UI designs are not committed as if implemented

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

## Independent final-commit review

- [ ] Reviewer inspected the actual diff, implementation and externally observed behavior, not only issue criteria or passing structural checks
- [ ] Reviewer checked documentation links, source-derived diagrams and provider evidence; unavailable mandatory acceptance remains **BLOCKED**
- [ ] Maintainer's explicit approval is required on the final SHA; neither a successful CI run nor an uploaded docs preview is deployment/merge approval

## Acceptance status

<!-- Distinguish VERIFIED, BLOCKED and OUT OF SCOPE. Never claim product readiness based only on green build checks. -->
