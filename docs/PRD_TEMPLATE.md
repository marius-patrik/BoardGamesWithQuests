# Product Requirements Document (PRD) — Reusable Template

> **Purpose:** Define **what** a product must achieve, **who** it serves, and **how** completion will be demonstrated. Copy this file for each product or release. Replace every [placeholder]; delete guidance that does not apply, or explicitly mark the section **Not applicable** with a reason. Do not present guesses as accepted decisions.
>
> **Depth:** For a small project, use the core sections and brief requirement cards. For a complex product, expand the optional domain, integration, operations, security, and migration sections. Keep one canonical requirement and link to detailed engineering designs instead of duplicating them.

## 0. Document control and authority

| Field | Value |
| --- | --- |
| Product / release | [Name and version] |
| Owner / decision maker | [Name or role] |
| Stakeholders / reviewers | [Roles] |
| Status | Draft / In review / Approved / Superseded |
| Version / last updated | [Version / YYYY-MM-DD] |
| Planning issue / delivery PRs | [Links] |
| Intended release / deadline | [Date or Undecided] |
| Governing source(s) | [Assignment, policy, customer evidence, approved contract] |
| Model / UX / technical spec | [Linked diagrams/specs and versions] |

**Authority rules:** Distinguish (A) externally prescribed requirements, (B) owner-approved decisions, (C) evidence-backed findings, (D) proposals and assumptions. A proposal is not a requirement until accepted. Note conflicts and seek a decision; never silently reconcile contradictory sources. This PRD owns product behavior and acceptance, not implementation task lists or code-level design.

## 1. Executive brief (one-page summary)

**Problem:** [What is wrong or missing, for whom, under what circumstances?]

**Why now / evidence:** [Specific source, observation or constraint; otherwise Unknown.]

**Users and primary job:** [Who uses the product and what they need to accomplish.]

**Desired outcome:** [User-visible change, not a list of features.]

**Proposed product approach:** [Short description; distinguish fixed constraints from revisable design.]

**Success test:** [How someone can verify that the product works.]

**Release boundary:** [What ships now; what is deliberately deferred.]

## 2. Context and source evidence

| ID | Source / link | Claim or constraint | Classification | Confidence / verification | Owner |
| --- | --- | --- | --- | --- | --- |
| SRC-001 | [Link] | [Statement] | Prescribed / Approved / Observed / Assumed | Confirmed / Pending | [Role] |

**Background:** [Prior product, environment, current workflow, reference implementation, constraints.]

**Assumptions to validate:** [Assumption, consequence if false, planned validation.] Never infer school/client requirements from a diagram without recording the interpretation.

**Glossary:** Define terms that can be confused, especially domain entities, user roles, state names, and metrics.

## 3. Users, stakeholders, and operating context

| Persona / role | Goal | Permissions / limitations | Environment | Evidence |
| --- | --- | --- | --- | --- |
| [Role] | [Outcome sought] | [Access and constraints] | [Device, context] | [Source] |

Record accessibility needs, supported platforms, offline/network assumptions, relevant skills, and any unusual environment. For small projects, one actual user and one demonstration scenario may suffice; do not invent personas.

## 4. Outcomes and success measures

| ID | Outcome | Metric or observable proof | Baseline | Target and window | Measurement method | Guardrail |
| --- | --- | --- | --- | --- | --- | --- |
| OBJ-001 | [Outcome] | [Measure] | [Known/Unknown] | [Quantified target or demonstrable condition] | [Test, observation, data] | [Unacceptable side effect] |

Prefer user outcomes to vanity metrics. If quantitative measures are inappropriate, use an objectively repeatable demonstration, such as completing an end-to-end task with specified expected results.

## 5. Scope and release boundaries

**Included (Must):** [Smallest complete set of necessary outcomes.]

**Should (time permitting):** [Valuable but nonblocking.]

**Could (optional):** [Only after Must and Should.]

**Explicitly excluded:** [Named non-goals, including tempting adjacent features.]

**Later releases:** [What is deferred, with an owner/source if known.]

**Constraints:** [Mandated languages, model diagrams, libraries, costs, time, platforms, legal/policy limits.] State which are negotiable.

**Cut rule:** If the deadline or budget is threatened, remove Could, then Should; do not silently weaken Must or its verification.

## 6. User journeys and behavior

Create a journey for every primary user goal and each critical failure/recovery path.

### FLOW-001 — [Journey name]
- **Actor and goal:** [Who does what and why.]
- **Preconditions:** [Required initial state.]
- **Trigger:** [Action or event.]
- **Main path:** [Numbered actor/system interactions and visible results.]
- **Alternatives:** [Valid variants.]
- **Failures and recovery:** [Invalid input, cancellation, timeout, interruption, conflicts.]
- **Postconditions:** [Persisted and visible result; what must remain unchanged.]
- **Linked requirements:** [FR IDs.]
- **Evidence:** [Demo, acceptance test or screenshot.]

For complex workflows, link a user-flow/state-machine diagram. Written flows and diagrams must agree.

## 7. Functional requirements

Each requirement is **atomic, necessary, unambiguous, feasible, and verifiable**. Use stable IDs, normative language and observable behavior. Keep implementation choices out unless explicitly mandated.

| ID | Priority | Requirement (observable system behavior) | Actor / trigger | Source / objective | Acceptance reference | Status |
| --- | --- | --- | --- | --- | --- | --- |
| FR-001 | Must | The system shall [one clear behavior and boundary]. | [Actor/event] | SRC-001 / OBJ-001 | AC-001 | Proposed |

### FR-[NNN] — [Short name]
- **User value:** [Why this matters.]
- **Preconditions and input:** [Data, permission, allowable ranges.]
- **Expected behavior and output:** [Observable response and state change.]
- **Invariants:** [What must always remain true.]
- **Alternative/invalid paths:** [What is rejected or recoverable, with expected feedback.]
- **State and persistence:** [What survives a restart, if applicable.]
- **Acceptance:** [At least one positive and one negative example; concrete expected result.]
- **Dependencies:** [Linked requirement or external constraint.]
- **Open questions:** [Do not invent an answer.]

### Acceptance example — AC-[NNN]
- **Given** [initial state and permissions],
- **When** [action/event],
- **Then** [observable result and any persisted effect],
- **And** [important invariant or non-effect].

Use enough examples to disambiguate boundaries; avoid tests that merely assert private method calls. Link requirements to verification evidence during implementation.

## 8. Domain model and system boundaries

**Use this section whenever a prescribed class diagram, data model, state machine, or architecture is part of the product contract. Model approval precedes implementation when the model is the assignment's central artifact.**

**Authoritative model:** [Diagram link, revision, status.]

**Design rule:** Prefer the prescribed model. Changes are permitted only with an explicit rationale grounded in behavior, correctness, or clarity.

| Model element | Prescribed purpose | Proposed responsibility | Relationships / invariants | Disposition | Rationale |
| --- | --- | --- | --- | --- | --- |
| [Class / entity] | [Reference UML] | [Single responsibility] | [Associations and ownership] | Preserve / Refine / Add / Remove | [Reason] |

**Responsibilities and ownership:** [Who owns mutable state, who validates, who may change it, who presents it.]

**Important state transitions:** [State, triggering action, guards, effects, terminal cases.]

**Data lifecycle:** [Creation, changes, deletion, persistence, recovery, privacy.]

**Diagram set (as applicable):** Class/domain UML; component boundaries; user-flow/activity; state machine; sequence for the most difficult interaction. Diagrams must be versioned and reviewed against each other and against requirements.

**Deviation register:** [Reference element, requested change, why required, impact, approval and date.] Do not call a deviation "implemented" until it is.

**Model walkthrough gate:** Each class/entity, association, state transition and critical rule can be explained in ordinary language, illustrated by a scenario, and traced to an actual requirement. No implementation begins while model-blocking questions remain unresolved.

## 9. User experience and interaction design

**Information architecture:** [Screens/areas and what belongs in each.]

**Interaction contract:** [Selection, navigation, editing, confirmation, cancellation, feedback and terminal states.]

**Design references:** [Wireframes, mockups, component or board visuals with version.]

**Accessibility and usability:** [Keyboard/pointer needs, focus, readable labels, contrast, resize, error recovery; specify only applicable requirements.]

**Critical state matrix:** [Empty, loading, normal, invalid, pending, completed, error/recovery.] Explain what the user sees and can do in each state.

**Usability demonstration:** [Actual tasks, target environment, observable criteria.]

## 10. Non-functional requirements

Include only relevant categories, but record why critical categories are not applicable. Make acceptance measurable rather than saying "fast", "secure", or "reliable".

| ID | Category | Requirement / measurable threshold | Context | Verification | Priority |
| --- | --- | --- | --- | --- | --- |
| NFR-001 | Performance | [e.g., action feedback within X ms on Y hardware] | [Scope] | [Method] | Must |
| NFR-002 | Reliability / integrity | [Failure and recovery invariant] | [Scope] | [Method] | Must |
| NFR-003 | Security / privacy | [Who can access/modify what] | [Scope] | [Method] | If applicable |
| NFR-004 | Compatibility | [Supported versions, devices, platforms] | [Scope] | [Method] | Must |
| NFR-005 | Maintainability | [Specific readability or support goal] | [Scope] | [Review/demo] | Should |
| NFR-006 | Accessibility | [Relevant accessible interactions] | [Scope] | [Manual/automated] | If applicable |

For complex systems consider concurrency, scale, availability, observability, retention, localization, compliance, resource ceilings and disaster recovery. Do not borrow enterprise requirements for a small local app.

## 11. Data, integrations, and interfaces (optional for complex projects)

**Data inventory:** [Entities, owner, identifier, sensitivity, retention, integrity rules, source of truth.]

**External dependencies:** [Provider, authentication, quotas, rate limits, SLA, failure behavior, cost and fallback policy.]

**Interface contracts:** [API/events/files, input and output schemas, versioning, permissions and error codes.] Link a separate versioned technical contract where appropriate.

**Concurrency:** [Race/conflict semantics, transaction boundary, idempotency, retry and consistency guarantees.]

**Migration and compatibility:** [Prior data versions, import/export, backfill, rollback, user impact.]

**Security/privacy:** [Threats, trust boundaries, least privilege, secrets and data exposure.]

If there is no network, external provider or persistent database, state "Not applicable" rather than inventing one.

## 12. Risks, tradeoffs, dependencies, and decisions

### Risk register
| ID | Risk / uncertainty | Impact | Likelihood | Mitigation or experiment | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| RISK-001 | [Concrete failure mode] | High/Med/Low | High/Med/Low | [Evidence-seeking action] | [Role] | Open |

### Dependencies
| ID | Prerequisite | Required for | Owner | Status / fallback |
| --- | --- | --- | --- | --- |
| DEP-001 | [Decision/component/provider] | [FR/phase] | [Role] | [Status] |

### Decision log
| ID / date | Decision | Alternatives | Rationale / evidence | Approver | Affected IDs |
| --- | --- | --- | --- | --- | --- |
| DEC-001 | [Accepted choice] | [Options considered] | [Why] | [Who] | [FR IDs] |

### Open questions
| ID | Question | Consequence if unresolved | Owner | Resolution needed by | Status |
| --- | --- | --- | --- | --- | --- |
| Q-001 | [Specific uncertainty] | [Blocked requirement] | [Role] | [Gate] | Open |

## 13. Delivery and verification plan

Keep this section at milestone/acceptance level; link the agent/execution plan for task ordering, branch choreography and implementation details.

| Milestone | Outcome / deliverable | Entry criteria | Exit evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| M1 — Requirements | [Approved scope] | [Evidence gathered] | [Reviewed PRD] | [Role] | Planned |
| M2 — Model | [Approved design] | [PRD agreed] | [Diagram review and scenario walkthrough] | [Role] | Planned |
| M3 — Functional | [Working feature set] | [Model signed off] | [Acceptance cases] | [Role] | Planned |
| M4 — Release | [Usable delivered product] | [Must requirements pass] | [End-to-end demo + distribution checks] | [Role] | Planned |

### Verification traceability matrix
| Requirement | Test/demo ID | Expected evidence | Actual result | Status | Reviewer |
| --- | --- | --- | --- | --- | --- |
| FR-001 | AC-001 / TEST-001 | [Observable output] | [Fill after run] | Not run / Pass / Fail / Blocked | [Role] |

**Definition of done:** All Must requirements have passing observable evidence at the final build; required non-functional limits are met; deferred items and accepted limitations are explicit; the demonstration matches the approved model. A passing build alone is not product acceptance.

## 14. Rollout, operations, and support (optional)

**Delivery vehicle:** [Source submission, installer, app store, web deployment, service migration, etc.]

**Release gates:** [Review approval, tests, packaging, docs, licenses, provenance, signing if required.]

**Rollout/reversal:** [Pilot, staged release, rollback or simple replacement.]

**Operations:** [Monitoring, support owner, backups/recovery, incident response if needed.]

**Postrelease feedback:** [Who evaluates the product, when, and how defects are triaged.]

## 15. Change history and review

| Version / date | Change | Reason | Impacted requirements/diagrams | Approved by |
| --- | --- | --- | --- | --- |
| 0.1 / [Date] | Initial draft | [Reason] | [IDs] | Pending |

**Review checklist**
- [ ] The problem, audience, outcome and current evidence are explicit.
- [ ] All prescribed constraints are traced; none were silently dropped.
- [ ] Must, Should, Could and out-of-scope boundaries are unambiguous.
- [ ] Every Must requirement has a stable ID, single behavior and verifiable acceptance.
- [ ] Main journey, invalid-input, cancellation, failure and terminal paths are covered.
- [ ] Domain model ownership, diagram relationships and invariants are internally consistent.
- [ ] Every deviation from a prescribed model is reasoned and approved.
- [ ] Relevant quality, privacy, persistence and platform constraints are measurable.
- [ ] No assumptions, speculative interfaces or unverified features are presented as completed.
- [ ] Open questions have owners; blocking questions are resolved before the affected milestone.
- [ ] The execution plan, model diagrams and PRD agree without duplicating conflicting authority.
- [ ] A human can demonstrate each core journey and explain how the model produces its result.

## 16. Research and method references

The structure combines concise agile product requirements with testable systems-engineering practice; it is a synthesis, not a claimed official standard template.

- Atlassian — [How to create a PRD](https://www.atlassian.com/agile/product-management/requirements/): concise context, objectives, assumptions, user stories, UX, open questions and exclusions.
- Productboard — [PRD guide](https://www.productboard.com/glossary/product-requirements-document/): outcomes, target users, scope, metrics, constraints and dependencies.
- Figma — [PRD guide](https://www.figma.com/resource-library/product-requirements-document/): journeys, designs, risk, quality and release criteria.
- NASA — [How to write a good requirement](https://www.nasa.gov/reference/appendix-c-how-to-write-a-good-requirement/): unique, clear, feasible, necessary and verifiable requirements.
- ISO/IEC/IEEE 29148:2018 — [Requirements engineering](https://www.iso.org/obp/ui?_escaped_fragment_=iso%3Astd%3Aiso-iec-ieee%3A29148%3Aed-2%3Av1%3Aen): formal context for requirements definition and management.

**Template maintenance rule:** Update this template when its structure fails to support a real planning need. Do not amend a live product PRD with invented requirements simply to fill the template.
