# Repository Engineering Rules

## Source authority

The PRD defines product requirements; architecture decisions define system
boundaries; PLAN defines unfulfilled work; SCRATCHPAD carries actionable work
notes. Source code, schema, tests, live services and independently reproduced
behavior determine whether a requirement is implemented. Never equate a
successful build, mock, screenshot or status label with working functionality.

## Timeless artifacts

Every committed artifact must describe only an authoritative contract,
implementation, decision, enduring requirement, or outstanding actionable task.
Never retain chronology, dated progress reports, version comparisons, migration
stories, abandoned designs, overwritten proposals, supersession notes, or
narratives about how the implementation used to work. Remove replaced material
instead of appending an explanation. Omit temporal qualifiers from headings,
links, comments and prose. Git commit history and issue discussions preserve
provenance. SQL migrations and immutable external assignment figures are
functional exceptions only to the extent required for reproducibility.

## Atomic artifact alignment — mandatory on every change

Treat each change as a dependency graph, not a source edit. In the same
implementation chunk, update **all affected artifacts**: public interfaces,
schemas, migrations, bundled JSON, engine and server behavior, frontend types,
documentation, architecture decisions, diagrams, usage examples, test fixtures,
behavioral tests, CI jobs, deployment configuration, issue/PR acceptance criteria
and release metadata. Delete stale references and redundant implementations.
Regenerate derived diagrams from source. Audit links and example commands.
Do not close a chunk, request review or merge while related artifacts disagree.
Never postpone corresponding behavior tests or docs synchronization to an
unspecified cleanup milestone. A PR must list impact surfaces and independent
reviewers verify the complete change graph.

## Behavior-driven testing contract

Tests must specify observable **inputs, actions and outcomes** through supported
interfaces: legal and illegal game actions, HTTP responses, database effects,
UI interactions, authentication decisions, event order, exported notation and
user-visible recovery. Prefer an external actor or black-box consumer viewpoint,
not assertions about code structure, class existence, imports, literals,
formatting, mocked call counts or private implementation details.

For every behavior change, cover:
- A representative successful user flow with explicit meaningful assertions.
- Boundary values and malformed/hostile input; failure must be safe and specific.
- Relevant state transitions, turn alternation, clocks, quests and terminal
  outcomes, with no state mutation on rejected operations.
- Identity isolation, wrong participant, missing permissions and revoked access.
- Race conditions, simultaneous submissions, duplicates, stale revisions and
  transaction rollback when shared mutable state is involved.
- Persistence after process restart, retries, lost messages and reconnect.
- A regression reproducing each resolved defect before the fix.

Use parametrized fixture scenarios for each game definition, including castling,
en passant, promotion and repetition; English capture chains; and international
maximal capture, backward captures, flying kings and capture obstruction.
Configuration tests must drive real JSON through the validator and interpreter.

Use test doubles only at genuinely nondeterministic third-party boundaries;
never mock the behavior being claimed as verified. Back each adapter contract
with real integration tests against its actual provider. Public network, browser
and database acceptance tests verify service behavior, not response shape alone.
If an external integration cannot run, mark the gate **blocked**; do not replace
it with a mocked pass or silently skip mandatory tests.

All tests must be deterministic, isolated, independent of execution order and
must clean up state. Tests must fail for an intentionally broken implementation.
Every scenario has a link to its requirement or documented defect. Include
independent adversarial review. Treat mutation/fault injection as additional
evidence where practical. A syntax check, import smoke test or bare compilation
never counts toward behavior acceptance.

Require test coverage with each production change. CI runs the real behavior
suite and fails if it is missing, skipped in place of mandatory coverage, or
reports unverified external requirements as passing. Run the relevant
integration and end-to-end gates before approving a production release.

## Architecture and security

All game-authored rules, boards, piece behavior, clocks, quests, hooks and
outcomes are bounded validated JSON, never executable Python/JavaScript,
eval/exec, dynamic imports or arbitrary extensions. The shared engine contains
only game-neutral trusted primitives and a single authoritative legal-commit
boundary. No game-identity special cases, implicit board dimensions or clock
defaults. The host verifies Supabase JWT identity, participant membership,
turn, legal state and expected revision before an atomic durable commit.
Supabase privileged credentials never reach public clients. Use participant-
scoped authorization, safe Realtime reconciliation and database RLS.

## Repository collaboration

Use focused Conventional Commits, an issue-bound integration PR and independent
review rounds. Keep `main` protected; no direct pushes or automatic integration
without maintainer approval. Keep one `repo.dfconfig` for DarkFactory. Native
build-tool metadata may exist where its ecosystem requires it; do not duplicate
authority. Keep workflows pinned to verified immutable versions. Preserve the
project boards, GPL licensing and supplied reference diagrams.

If an external operation is blocked or a new paid resource is required,
continue independent work and record the actual blocker without fabricating
success. Require green relevant CI, behavioral evidence, security review and
maintainer approval before deployment is declared complete.
