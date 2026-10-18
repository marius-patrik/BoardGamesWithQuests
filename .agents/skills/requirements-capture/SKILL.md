---
name: requirements-capture
description: Capture future product requirements in GitHub issues; document supported behavior only once implemented.
---
# Requirements Capture

## When to use

When the maintainer requests a new capability or changes its desired contract.

## Procedure

1. Inspect the current code and [master issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348).
2. Record **future** behavior, API/DB/DSL/UX contracts, acceptance criteria and dependencies only in the owning GitHub issue; technical ratification belongs to #350.
3. Reconcile contradictory issue requirements before implementation; do not copy them into `.agents/requests/`, PRD, decisions, or actual-code diagrams.
4. During the implementing PR, verify actual external behavior first, then update the relevant approved `.agents/requests/` record to describe **only the implemented subset**, with affected decisions/rules/notes.
5. Regenerate the four governed documents and run their consistency check; leave unimplemented scope open in issues.

## Evidence

Traceable issue decisions, implemented source/tests and matching commit-generated documentation. Issue approval is never runtime acceptance.
