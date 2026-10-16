## Scope and contract

<!-- State the independently usable responsibility delivered; reference the authoritative requirement/plan. -->

## Linked issue

<!-- Use the actual tracked issue number; the repository workflow enforces binding. -->
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

## Artifact alignment

- [ ] APIs, implementations, configuration, schemas, migrations, game JSON, tests, documentation and diagrams agree
- [ ] Links, example commands, issue criteria, deployment and release metadata updated where affected
- [ ] No unused parallel authority, fake readiness, disposable scaffold or historical commentary introduced
- [ ] No credentials or privileged operations exposed to public clients
- [ ] Independent reviewer has checked implementation, security and actual acceptance evidence
- [ ] Draft remains unmerged pending explicit maintainer approval

## Acceptance status

<!-- Distinguish VERIFIED, BLOCKED and OUT OF SCOPE. Never claim product readiness based only on green build checks. -->
