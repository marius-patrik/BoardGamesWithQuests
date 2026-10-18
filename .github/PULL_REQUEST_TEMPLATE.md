## Scope and contract

<!-- State only functionality genuinely implemented in this PR. Prospective API/DB/DSL/UI/game contracts, target diagrams and acceptance criteria belong in the linked GitHub issue, not repository PRD/architecture files. -->

## Linked issue

<!-- Bind with Closes #NUMBER, Fixes #NUMBER or Resolves #NUMBER (not a bare issue hyperlink). The CI enforces it. -->
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

- [ ] **Fact-only docs:** every claim in README/PRD/ARCHITECTURE/AGENTS, diagrams, generated code documentation and examples is supported by source or observable behavior **in this PR's exact commit**; future designs remain in GitHub issues
- [ ] **Same-PR synchronization:** every affected authored governance record, generated projection, tests, CI and deployment description was updated in this PR, not deferred to follow-up cleanup
- [ ] **No prospective contract files:** proposed endpoints/DTOs, relational schemas, DSL/operator registries, game definitions, target source trees and UI mockups are kept only in issues until genuinely implemented

- [ ] Updated any affected `.agents/{notes,requests,decisions,rules}/` source record and regenerated README, PRD, ARCHITECTURE and AGENTS in one diff
- [ ] `python3 .github/scripts/generate_documents.py --check` passes, including symlinks, submodule and `.github/tests/` ownership
- [ ] The **actual** branch policy is described correctly: current native #331 → #343 → #271 stack targets existing `main`; the proposed `develop` cutover, branch protection and release-trigger hardening remain unexecuted work in #404. DarkFactory PrideVer is the accepted versioning authority; no unrequested release or promotion.

## Artifact alignment

- [ ] APIs, implementations, configuration, schemas, migrations, game JSON, tests, documentation and diagrams agree
- [ ] Links, example commands, issue criteria, deployment and release metadata updated where affected
- [ ] No unused parallel authority, fake readiness, disposable scaffold or historical commentary introduced
- [ ] No credentials or privileged operations exposed to public clients
- [ ] Independent reviewer has checked implementation, security and actual acceptance evidence
- [ ] Draft remains unmerged pending explicit maintainer approval

## Independent review checklist

- [ ] Reviewer compared every significant capability and governance assertion against the **actual final commit**, not the proposed issue design
- [ ] Reviewer checked links, tracked-source diagrams, generated governance and source ownership; **no future implementation presented as shipped**
- [ ] Reviewer examined external acceptance evidence and recorded any unverified capability as BLOCKED; approval and merge remain maintainer-only

## Acceptance status

<!-- Distinguish VERIFIED, BLOCKED and OUT OF SCOPE. Never claim product readiness based only on green build checks. -->
