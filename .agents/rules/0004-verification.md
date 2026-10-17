---
status: active
---
# Verification and evidence

- Identify actual build, formatting, type-check, test and documentation commands from the repository, not assumptions.
- Verify the smallest relevant scope while developing, then all affected integration paths before reporting completion.
- Add or update behavioral tests for implementation changes. If tests are absent, state that limitation and do not substitute compilation for behavioral evidence.
- For UI or deployed behavior, confirm the real interaction or runtime result; passing unit tests alone cannot prove a working interface.
- Do not weaken quality gates, manufacture passing results or ignore failing checks. Surface and fix defects with reproducible evidence.
- Before merging, revalidate against the current integration branch and inspect the final diff for unintended files.

### BoardGamesWithQuests: Externally Observable Verification
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

### BoardGamesWithQuests: Verification and CI
Run the genuine applicable behavior suite and independent adversarial review
with every production change. Required status checks must accurately reflect
their actual coverage. Typechecking, formatting, compilation, documentation
and packaging are valid engineering checks but never substitute for a missing
external behavior or security acceptance gate. Do not weaken required checks
to manufacture a green PR.
