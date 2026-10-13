# Repository Development Rules

## Evidence and safety
Report verification accurately. Compilation, documentation generation, formatting,
type checks and smoke checks never establish product behavior. Do not merge known
incorrect interim implementations or advertise unavailable features. Reject unsafe
inputs explicitly and keep unfinished work isolated from supported paths.

## Source of truth and documentation
Product requirements live in the PRD, architecture decisions in the object model,
delivery sequencing in the Plan and transient verification state in the scratchpad.
Keep active documentation **forward-looking and evergreen**: no historical narration,
migration chronicles, superseded instructions, past milestones, stale dates or
temporary issue/PR numbers. Preserve provenance in Git history and issue discussions.
Remove completed migration tasks from active instructions. Do not replace a general
rule with an explanation of a one-time event. Never duplicate a plan in another file.
Preserve immutable external assignment/reference material exactly as supplied.

## Documentation quality and naming
Write code and documentation in English, with Google-style docstrings and type
annotations as appropriate. Generate documentation from tracked sources and fail
the strict documentation build on warnings. Never commit generated docs source.
Compare design changes against the preserved reference diagram and document each
intentional architectural deviation with its rationale.

## Contributions, branches and review
Never push directly to protected main. Use focused Conventional Commits of the form
`type(scope): subject` (feat, fix, refactor, test, docs, chore, ci).
Keep PRs draft until ready; require green applicable checks, an up-to-date base,
independent implementation review and explicit native maintainer approval.
Every PR binds the appropriate tracked issue and reconciles plan deviations before
merging. Use bot-authored PRs through the installed DarkFactory pipeline when owner
approval requires a distinct author identity.

## Planning and traceability
New independent requests normally get a Request issue preserving the original
user text plus an explicit interpretation; require confirmation before scheduling
implementation. Create a child Plan issue tied to the request when supported.
A maintainer-approved consolidation may use an existing Plan issue without
duplicating the backlog. Record acceptance evidence against requirements;
do not treat issue closure as proof that tests or deployment passed.

## CI and automation
Keep a single DarkFactory configuration at `repo.dfconfig`; retain Python
packaging and tool-specific configuration files where the corresponding tools
require them. Agent runners and approval logic should be shared, pinned to
immutable verified releases; this repository owns only thin callers and genuinely
project-specific verification. Stable checks include `quality` and
`verify-bound-issue` plus applicable docs, Python, browser, security and API
tests. Do not substitute compilation for functional test coverage without
explicitly marking that absence. Keep every integration review thread addressed
before requesting approval. Preserve the established project boards and taxonomies.

## Domain and security architecture
Games, movements, rules, hooks, quests, clocks, configuration and outcomes are
validated bounded JSON. Never allow user-authored executable Python, JavaScript,
dynamic plugin imports, arbitrary expressions or eval. Implement only trusted
generic primitives in the engine, without branches on game identities. Provide
all game-significant values explicitly. Only an authoritative game transaction
may authorize and commit state changes; user/profile managers cannot mutate
boards. Every hosted mutation verifies the authenticated identity, participant
membership, current revision and legal state, then commits atomically and durably.
Never expose Supabase secret/service credentials to clients. Enforce participant-
scoped RLS and safe Realtime resynchronization, including anonymous guests.

## Verification gates
Cover negative cases, simultaneous actions and the real user-visible workflow.
If a package or external service cannot be validated, record an explicit blocker
rather than claiming completion. Enforce required status checks and review gates
before final merge or a public playable release.
